import threading
import time

from obs.integrator_bridge import BaseHolyricsOBSBridge


class HolyricsOBSController:
    def __init__(self, bridge: BaseHolyricsOBSBridge):
        self.bridge = bridge
        self.thread = None
        self.running = False

    def start(self):
        """
        Inicia o integrador em uma thread separada.
        """
        if self.running:
            print('⚠️ Bridge already running.')
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_bridge, daemon=True)
        self.thread.start()
        print('✅ Bridge started.')

    def stop(self):
        """
        Solicita o encerramento do integrador.
        """
        if not self.running:
            print('⚠️ Bridge is not running.')
            return

        self.running = False
        self.thread.join(timeout=1)
        print('🛑 Bridge stop requested.')

    def is_running(self) -> bool:
        """
        Verifica se o integrador está em execução.
        """
        return self.running

    def _run_bridge(self):
        """
        Loop de execução que respeita o sinal de parada.
        """
        try:
            while self.running:
                self.bridge.run()

                time.sleep(1)
        except KeyboardInterrupt:
            print('\n🛑 Stopped by user.')
        except Exception as e:
            print(f'❌ Error in bridge thread: {e}')
