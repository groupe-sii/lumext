# LUMext UI

## Installation

See [README.md](../) of the main project.

## Build `plugin.zip`

To get `plugin.zip` you need to construct `/dist` folder

### What contains `/dist` folder ?

In `/dist` you will find all UI :

* folder `assets` with translations (empty in our case).
* `bundle.js`: all the project UI translates in JavaScript.
* `i18n.json`: translation of menu.
* `manifest.json`: description of UI extension.
* `plugin.zip`: ZIP of all previous files.

### Pre-requisites

* NodeJS
* Yarn
* A clone of the project

### Get dependencies

To Install all dependencies:

```bash
yarn install
```

### Build `/dist` with `plugin.zip`

Use yarn's build command

```bash
yarn run build
```

The `/dist` will be created automatically in the current folder with `plugin.zip` in.

### Full example of build process on Ubuntu

Clone the project:

```bash
git clone https://github.com/groupe-sii/lumext.git lumext-app
cd lumext-app/ui
```

Install node and npm:

```bash
sudo apt install nodejs npm curl
```

Install Yarn:

```bash
sudo curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
sudo apt-get update && sudo apt-get install yarn
```

Build dependencies (in the folder project):

```bash
yarn install
```

Build `/dist` with `plugin.zip`:

```bash
yarn run build
```