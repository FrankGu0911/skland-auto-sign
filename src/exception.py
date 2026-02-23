"""异常类定义"""


class Exception(Exception):
    """异常基类"""
    pass


class RequestException(Exception):
    """请求错误"""
    pass


class UnauthorizedException(Exception):
    """登录授权错误"""
    pass


class LoginException(Exception):
    """登录错误"""
    pass
