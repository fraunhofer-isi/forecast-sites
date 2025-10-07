// © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import globals from "globals";
import pluginJs from "@eslint/js";
import unusedImports from "eslint-plugin-unused-imports";
import unicorn from "eslint-plugin-unicorn";
import checkfile from "eslint-plugin-check-file";
import jest from "eslint-plugin-jest";


export default [
  {
    ignores: ["coverage/*"],
  },
  {
    files: ["src/*.js"],
    languageOptions: {
      sourceType: "script",
    },
  },
  {
    files: ["test/*.js"],
    languageOptions: {
      sourceType: "script",
    },
  },
  {
     languageOptions: {
       globals: Object.assign(
        {
          global: "readonly",
          require: "readonly"
        },
        globals.browser,
        globals.jest),
       ecmaVersion: 2015,
        sourceType: "module",
     },
     plugins: {
        jest,
        unicorn,
        "check-file": checkfile,
        "unused-imports": unusedImports,
    },

    rules: {
        "unicorn/filename-case": [
          "error",
          {
            "case": "camelCase", // or "camelCase", "snake_case", etc.
          },
        ],
        "check-file/folder-naming-convention": [
          'error',
          {
              'src/**/': 'SNAKE_CASE',
              "test/**/": "SNAKE_CASE"
          }
        ],

        camelcase: "error",
        "jsdoc/require-jsdoc": "off",
        "jsx-a11y/label-has-associated-control": "off",
        "jsx-a11y/control-has-associated-label": "off",
        "keyword-spacing": "off",
        "linebreak-style": ["error", "unix"],

        "max-len": ["error", {
            code: 120,
        }],

        "max-lines": [1, {
            max: 300,
            skipBlankLines: true,
            skipComments: true,
        }],

        "no-undef": "off",
        "no-console": "off",
        "no-else-return": "off",
        "no-underscore-dangle": "off",
        "no-unused-vars": "off",
        "no-plusplus": "off",
        "no-restricted-syntax": "off",
        "no-param-reassign": "off",
        "no-continue": "off",

        semi: ["error", "always", {
            omitLastInOneLineBlock: false,
        }],

        "semi-style": ["error", "last"],
        "no-extra-semi": ["error"],

        "semi-spacing": ["error", {
            before: false,
            after: true,
        }],

        "sonarjs/prefer-immediate-return": "off",
        "space-before-blocks": "off",
        "space-before-function-paren": "off",
        "unicorn/no-static-only-class": "off",

        "unused-imports/no-unused-vars": ["warn", {
            vars: "all",
            varsIgnorePattern: "^_",
            args: "after-used",
            argsIgnorePattern: "^_",
        }],

        "unused-imports/no-unused-imports": "error",
    },
  },
  pluginJs.configs.recommended

];