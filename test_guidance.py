from guidance import GUIDANCE, all_root_components_present


def test_all_root_components_present():
    result = dict(has_pyproject=True, has_gitignore=True, has_tests=True, has_ci=True)
    assert all_root_components_present(result)


def test_nested_components_do_not_count_as_root():
    result = dict(has_pyproject=True, has_gitignore=False, has_tests=True, has_ci=True,
                  gitignore_files=['src/.gitignore'])
    assert not all_root_components_present(result)


def test_missing_result_keys_do_not_trigger_celebration():
    assert not all_root_components_present({})


def test_guidance_has_required_sections():
    assert set(GUIDANCE) == {'pyproject', 'gitignore', 'tests', 'ci'}
    for guidance in GUIDANCE.values():
        for key in ('title', 'what', 'why', 'how', 'example', 'language'):
            assert guidance[key]
