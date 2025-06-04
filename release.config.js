export default {
  branches: [{ name: "main" }],
  plugins: [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    [
      "@semantic-release/changelog",
      {
        changelogFile: "CHANGELOG.md",
      },
    ],
    [
      "@semantic-release/exec",
      {
        prepareCmd: "sed -i 's/^version = \".*\"/version = \"${nextRelease.version}\"/' pyproject.toml"
      }
    ],
    [
      "@semantic-release/git",
      {
        assets: ["CHANGELOG.md", "pyproject.toml"],
        message: "chore(release): ${nextRelease.version} [skip ci]"
      }
    ],
    "@semantic-release/github",
  ],
};
