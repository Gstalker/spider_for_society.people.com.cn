
class Log:
    @staticmethod
    def v(fmt : str) -> None:
        print("[VERB]: " + fmt)
    @staticmethod
    def e(fmt:str,*args) -> None:
        print("[ERR!]: " + fmt)
    @staticmethod
    def succ(fmt:str) -> None:
        print("[SUCC]: " + fmt)