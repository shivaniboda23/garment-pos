```
c:\Users\SHIVANI\Projects\garment-pos
├───.gitignore
├───backend.zip
├───docker-compose.yml
├───garments-pos_clean1.zip
├───GEMINI.md
├───LICENSE
├───mobile_app.zip
├───package-lock.json
├───package.json
├───README.md
├───.git\...
├───assets
│   ├───icons
│   ├───logos
│   └───screenshots
├───backend
│   ├───alembic.ini
│   ├───requirements.txt
│   ├───run.py
│   ├───alembic
│   │   ├───env.py
│   │   ├───README
│   │   ├───script.py.mako
│   │   ├───__pycache__\...
│   │   └───versions
│   ├───app
│   │   ├───dependencies.py
│   │   ├───main.py
│   │   ├───__pycache__\...
│   │   ├───api
│   │   ├───core
│   │   ├───crud
│   │   ├───db
│   │   ├───dependencies
│   │   ├───models
│   │   ├───schemas
│   │   ├───services
│   │   └───utils
│   ├───tests
│   └───venv
│       ├───pyvenv.cfg
│       ├───Include
│       ├───Lib
│       └───Scripts
├───backend-express
│   ├───package-lock.json
│   ├───package.json
│   ├───requirements.txt
│   ├───server.js
│   ├───app
│   │   ├───main.py
│   │   ├───api
│   │   ├───auth
│   │   ├───config
│   │   ├───core
│   │   ├───database
│   │   ├───middleware
│   │   ├───models
│   │   ├───repositories
│   │   ├───schemas
│   │   ├───services
│   │   └───utils
│   ├───config
│   │   └───db.js
│   ├───controllers
│   │   ├───categoryController.js
│   │   ├───invoiceController.js
│   │   ├───productController.js
│   │   ├───schoolController.js
│   │   ├───stockController.js
│   │   └───supplierController.js
│   ├───node_modules\...
│   └───routes
│       ├───categories.js
│       ├───invoices.js
│       ├───productRoutes.js
│       ├───products.js
│       ├───schoolRoutes.js
│       ├───stockRoutes.js
│       └───suppliers.js
├───database
│   ├───schema.sql
│   ├───seed.sql
│   └───migrations
├───docs
│   ├───API.md
│   ├───Architecture.md
│   ├───Database.md
│   └───UserManual.md
├───frontend
│   ├───.gitignore
│   ├───eslint.config.js
│   ├───index.html
│   ├───package-lock.json
│   ├───package.json
│   ├───README.md
│   ├───vite.config.js
│   ├───node_modules\...
│   ├───public
│   │   ├───favicon.svg
│   │   └───icons.svg
│   └───src
│       ├───App.css
│       ├───App.jsx
│       ├───index.css
│       ├───main.jsx
│       ├───assets
│       ├───components
│       ├───config
│       ├───context
│       ├───hooks
│       ├───pages
│       ├───reducers
│       ├───routes
│       ├───services
│       ├───styles
│       ├───theme
│       └───utils
├───garment-pos
├───garments-pos_clean
│   ├───backend
│   │   ├───package-lock.json
│   │   ├───package.json
│   │   ├───requirements.txt
│   │   ├───server.js
│   │   ├───app
│   │   ├───config
│   │   ├───controllers
│   │   └───routes
│   └───frontend
│       ├───eslint.config.js
│       ├───index.html
│       ├───package-lock.json
│       ├───package.json
│       ├───README.md
│       ├───vite.config.js
│       ├───public
│       └───src
├───mobile_app
│   ├───.gitignore
│   ├───.metadata
│   ├───analysis_options.yaml
│   ├───pubspec.lock
│   ├───pubspec.yaml
│   ├───README.md
│   ├───.dart_tool\...
│   ├───.idea\...
│   ├───android
│   │   ├───.gitignore
│   │   ├───build.gradle.kts
│   │   ├───gradle.properties
│   │   ├───settings.gradle.kts
│   │   ├───.gradle\...
│   │   ├───.kotlin
│   │   ├───app
│   │   └───gradle
│   ├───build\...
│   ├───ios
│   │   ├───.gitignore
│   │   ├───Flutter
│   │   ├───Runner
│   │   ├───Runner.xcodeproj
│   │   ├───Runner.xcworkspace
│   │   └───RunnerTests
│   ├───lib
│   │   ├───main.dart
│   │   ├───constants
│   │   ├───models
│   │   ├───providers
│   │   ├───screens
│   │   ├───services
│   │   ├───theme
│   │   ├───utils
│   │   └───widgets
│   ├───linux
│   │   ├───.gitignore
│   │   ├───CMakeLists.txt
│   │   ├───flutter
│   │   └───runner
│   ├───macos
│   │   ├───.gitignore
│   │   ├───Flutter
│   │   ├───Runner
│   │   ├───Runner.xcodeproj
│   │   ├───Runner.xcworkspace
│   │   └───RunnerTests
│   ├───test
│   │   └───widget_test.dart
│   ├───web
│   │   ├───favicon.png
│   │   ├───index.html
│   │   ├───manifest.json
│   │   └───icons
│   └───windows
│       ├───.gitignore
│       ├───CMakeLists.txt
│       ├───flutter
│       └───...
├───node_modules\...
├───scripts
└───tests

## Stock Architecture

These rules are ABSOLUTE.

1.  Never use `product.stock`.
2.  Never use `bucket_type`.
3.  One Stock row belongs to exactly one ProductVariant.
4.  Never update `stock.quantity`.
5.  `quantity` is a property only.
6.  Update only `k_stock` and `r_stock`.
7.  UI may display `stock.quantity` or `k_stock + r_stock`.
8.  ProductVariant owns inventory.
9.  Product never owns inventory.
10. Never redesign this architecture.

## Migration Rules (ABSOLUTE)

The architecture is frozen.

Never introduce temporary architectures.

Never create compatibility layers unless explicitly instructed.

Never assume a Product has one ProductVariant.

Never guess a ProductVariant.

If a module cannot determine the correct ProductVariant,
STOP.

Report the architectural dependency.

Wait for approval.

Never invent business logic to continue.

Every inventory movement must reference ProductVariant.

Stock is always updated through ProductVariant.

Legacy Product stock fields exist only during migration.

No new code may read or write Product.k_stock or Product.r_stock.

Remove legacy code only after every dependent module has been migrated.

## Business Rule Discovery

When architecture is insufficient to implement a module:

DO NOT assume business behavior.

Instead:

1. Identify the missing rule.
2. Explain why implementation depends on it.
3. Present all reasonable implementation options.
4. Wait for approval.

Never choose one option yourself.

# Approved Business Rules
Product and ProductVariant are created separately.

A Product may exist without variants.

Stock is created immediately when a ProductVariant is created.

Initial Stock:
k_stock = 0
r_stock = 0

Only Purchase increases stock.

Only Billing/Sales decrease stock.

SKU is entered by the user.

Barcode is entered by the user.

PurchaseItem references ProductVariant.

SaleItem references ProductVariant.

BillItem references ProductVariant.
## Patch Workflow

Every generated patch must follow this order:

1. Audit
2. Wait for approval
3. Generate patch
4. Wait for user to Accept
5. Stop

Never continue to the next module automatically.

Never assume a patch has been applied.

Treat an accepted patch as the new codebase.

All future audits must use the accepted code as the baseline.