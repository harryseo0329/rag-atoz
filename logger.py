import logging

#CRITICAL = 50
#FATAL = CRITICAL
#ERROR = 40
#WARNING = 30
#WARN = WARNING
#INFO = 20
#DEBUG = 10
#NOTSET = 0

# 사용자 정의 로그 레벨
CUSTOM_LEVEL = 60
logging.addLevelName(CUSTOM_LEVEL, "CUSTOM")

# 사용자 정의 로그 메서드
def log_custom(self, message, *args, **kws):
    if self.isEnabledFor(CUSTOM_LEVEL):
        self._log(CUSTOM_LEVEL, message, args, **kws)

def log_error(self, message, *args):
        print(f"[ERROR LOG] {message % args if args else message}")

# Logger 클래스에 메서드 추가
logging.Logger.log_custom = log_custom
logging.Logger.log_error = log_error

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)