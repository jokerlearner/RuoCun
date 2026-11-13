"""冻结 run.tsx (MIT) 入口；复用调用者持有的终端，流程完成后由调用者接续。"""

from .onboarding import Onboarding as runOnboarding
from .onboarding import OnboardingResult as OnboardingResult

__all__ = ["OnboardingResult", "runOnboarding"]
