import unittest

from generate_changelog import Commit, classify_commit, parse_github_repo, render_changelog


class GenerateChangelogTests(unittest.TestCase):
    def test_parses_github_repo_values(self):
        self.assertEqual(parse_github_repo("owner/repo"), ("owner", "repo"))
        self.assertEqual(parse_github_repo("https://github.com/owner/repo.git"), ("owner", "repo"))

    def test_classifies_common_commit_styles(self):
        cases = {
            "feat: add billing dashboard": "Added",
            "fix(api): prevent null response crash": "Fixed",
            "remove deprecated sqlite adapter": "Removed",
            "docs: clarify setup": "Changed",
        }
        for subject, category in cases.items():
            with self.subTest(subject=subject):
                self.assertEqual(classify_commit(Commit(sha="abc1234", subject=subject)), category)

    def test_renders_only_populated_sections(self):
        output = render_changelog(
            [
                Commit(sha="abc1234", subject="feat: add export command", author="Ada"),
                Commit(sha="def5678", subject="fix: correct date heading", author="Grace"),
            ],
            since_tag="v1.0.0",
            source="github.com/example/repo",
        )
        self.assertIn("### Added", output)
        self.assertIn("### Fixed", output)
        self.assertNotIn("### Removed", output)
        self.assertIn("Generated from `github.com/example/repo` since `v1.0.0`.", output)


if __name__ == "__main__":
    unittest.main()
