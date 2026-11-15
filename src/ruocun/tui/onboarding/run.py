"""提供首次引导的会话入口，复用调用者已持有的终端，结束后由调用者接续。"""

from .onboarding import Onboarding as runOnboarding
from .onboarding import OnboardingResult as OnboardingResult

__all__ = ["OnboardingResult", "runOnboarding"]
