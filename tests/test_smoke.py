"""冒烟测试：验证 zhixing 包可正常导入且版本号正确。"""


def test_import_and_version():
    import zhixing

    assert zhixing.__version__ == "0.1.0"
