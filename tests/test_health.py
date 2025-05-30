import logging

def test_logging_info():
    """测试日志输出功能"""
    try:
        logging.info("测试日志输出：info 级别")
    except Exception as e:
        assert False, f"日志输出异常: {e}" 