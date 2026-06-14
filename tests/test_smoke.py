def test_package_imports():
    import chotic_ui
    assert hasattr(chotic_ui, "clear_screen")
