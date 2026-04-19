/* ESLint config for the TopicVisExplorer frontend. The legacy/ directory is
 * excluded from lint because those files are vendored verbatim from the
 * paper version (LDAvis, topicflow, sankey) and re-formatting them would
 * make visual-regression diffing harder. */
module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: "module",
  },
  plugins: ["@typescript-eslint"],
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  env: {
    browser: true,
    es2020: true,
    node: true,
  },
  ignorePatterns: ["dist/", "node_modules/", "src/legacy/**"],
  rules: {
    "@typescript-eslint/no-explicit-any": "off",
    "@typescript-eslint/no-unused-vars": [
      "warn",
      { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
    ],
    "no-undef": "off",
  },
};
