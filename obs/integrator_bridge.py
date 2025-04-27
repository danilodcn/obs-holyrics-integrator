import abc
import time
import urllib.parse as urlparse

import httpx
import obsws_python as obs
import requests


class BaseHolyricsOBSBridge(abc.ABC):
    def run(self):
        raise NotImplementedError()


class HolyricsOBSBridge(BaseHolyricsOBSBridge):
    def __init__(
        self,
        obs_host: str,
        holyrics_host: str,
        principal_scene: str,
        holyrics_scene: str,
    ):
        self.principal_scene = principal_scene
        self.holyrics_scene = holyrics_scene
        self.current_scene: str | None = None
        self.holyrics_client = httpx.Client(base_url=holyrics_host)

        obs_url_parsed = urlparse.urlparse(obs_host)
        obs_host_port = obs_url_parsed.port
        obs_host_hostname = obs_url_parsed.hostname

        # Conexão com o OBS WebSocket
        self.obs_client = obs.ReqClient(
            host=obs_host_hostname, port=obs_host_port, password=''
        )
        import ipdb

        ipdb.set_trace()  # noqa: E701

    def _has_holyrics_text(self) -> bool:
        """
        Busca o texto atual do Holyrics.
        """
        try:
            response = self.holyrics_client.get('/view/text.json', timeout=1)
            response.raise_for_status()
            data: dict = response.json()
            map = data.get('map', {})
            text = map.get('text', '').strip()
            type = map.get('type', '')

            if bool(text):
                if type == 'MUSIC':
                    music_is_active = set(map.keys()).intersection(
                        {
                            '$system_var_music_artist',
                            '$system_var_music_author',
                            '$system_var_music_copyright',
                            '$system_var_music_title',
                        }
                    )
                    return music_is_active
                if type == 'BIBLE':
                    bible_is_active = map.get('header', '') != ''

                    return bible_is_active

            return False
        except (requests.RequestException, ValueError):
            # Em caso de erro na conexão ou no JSON, trata como sem texto
            return False

    def switch_scene(self, scene_name: str):
        """
        Troca de cena no OBS, apenas se a cena atual for diferente.
        """
        if self.current_scene != scene_name:
            self.obs_client.set_current_program_scene(scene_name)
            self.current_scene = scene_name
            print(f'✅ Switched scene to: {scene_name}')

    def run(self):
        """
        Loop principal que faz a ponte entre Holyrics e OBS.
        """
        print('🚀 Starting Holyrics to OBS bridge...')
        try:
            while True:
                has_text = self._has_holyrics_text()

                if has_text:
                    print(
                        f'🎤 Holyrics is active. Switching to Holyrics scene {self.holyrics_scene}'
                    )
                    self.switch_scene(self.holyrics_scene)
                else:
                    print(
                        f'📖 Holyrics is inactive. Switching to principal scene {self.principal_scene}'
                    )
                    self.switch_scene(self.principal_scene)

                time.sleep(1)

        except KeyboardInterrupt:
            print('\n🛑 Stopped by user.')
        except Exception as e:
            print(f'❌ Error: {e}')
            raise e
        finally:
            self.obs_client.disconnect()
            print('🔌 OBS connection closed.')


# Exemplo de uso
if __name__ == '__main__':
    bridge = HolyricsOBSBridge(
        obs_host='http://localhost:4455',  # Endereço do OBS WebSocket
        holyrics_host='http://localhost:8080',  # Endereço do Holyrics
        principal_scene='palavra',
        holyrics_scene='palavra/biblia',
    )
    bridge.run()
