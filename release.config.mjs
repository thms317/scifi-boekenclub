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
        prepareCmd: "uv version ${nextRelease.version} --no-sync"
      }
    ],
    [
      "@semantic-release/git",
      {
        assets: ["CHANGELOG.md", "pyproject.toml", "uv.lock"],
        message: "chore(release): ${nextRelease.version} [skip ci]"
      }
    ],
    "@semantic-release/github",
  ],
};
