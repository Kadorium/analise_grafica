# Frontend Developer Guide: AI-Powered Trading Analysis System

## Overview

This document is the **primary guide** for understanding, developing, and maintaining the frontend of the AI-Powered Trading Analysis System. It details the architecture, modularity, and workflow, explaining how the frontend (HTML, CSS, JavaScript) interacts with the Python FastAPI backend (`app.py`), how the UI is structured (`frontend/index.html`), and how the JavaScript modules (rooted in `frontend/js/main.js`) orchestrate the user experience and API communications.

**It is CRUCIAL that any developer making modifications to the frontend structure, modules, parameters, API interactions, or overall workflow updates this document accordingly. This ensures the guide remains accurate and useful for all team members, including AI-driven development processes.**

---

## Table of Contents

- [Architecture & Modularity](#architecture--modularity)
- [Frontend-Backend Connection](#frontend-backend-connection)
  - [Backend Role (`app.py`)](#backend-role-apppy)
  - [Frontend Role](#frontend-role)
- [Key Files & Their Roles](#key-files--their-roles)
- [UI Structure & Navigation](#ui-structure--navigation)
  - [Tabbed Interface](#tabbed-interface)
  - [Dynamic Content Loading](#dynamic-content-loading)
- [JavaScript Module System](#javascript-module-system)
  - [Core Modules (`frontend/js/modules/`)](#core-modules-frontendjsmodules)
  - [Utility Modules (`frontend/js/utils/`)](#utility-modules-frontendjsutils)
- [State Management (`appState`)](#state-management-appstate)
- [API Communication (`utils/api.js`)](#api-communication-utilsapijs)
- [How to Extend or Modify](#how-to-extend-or-modify)
  - [Adding a New UI Section/Feature](#adding-a-new-ui-sectionfeature)
  - [Modifying Existing Features or Parameters](#modifying-existing-features-or-parameters)
  - [Updating API Interactions](#updating-api-interactions)
- [Testing & Debugging](#testing--debugging)
  - [Frontend Logger (`AppLogger`)](#frontend-logger-applogger)
- [Best Practices](#best-practices)
- [Contributing & Coordination](#contributing--coordination)
- [Glossary](#glossary)
- [**Update Policy (Mandatory)**](#update-policy-mandatory)
- [Changelog Template](#changelog-template)
- [Deprecated/Legacy Files](#deprecated-legacy-files)
- [LLM/AI Contributor Rule](#llm-ai-contributor-rule)

---

## Architecture & Modularity

- **Frontend**: A single-page application (SPA) built with pure HTML, CSS (Bootstrap for styling and layout), and modern JavaScript (modular ES6). Chart.js is used for interactive charts.
- **Backend (`app.py`):** A Python application using the FastAPI framework. It exposes a comprehensive set of RESTful API endpoints that the frontend consumes for all trading analysis, data processing, strategy execution, optimization, and configuration management tasks.
- **Communication**: The frontend interacts with the backend exclusively through asynchronous HTTP requests (fetch API) to these `/api/*` endpoints. Responses are typically JSON, with chart images often sent as base64 encoded strings.
- **Modularity**: The frontend JavaScript is highly modular. Each major functional area or UI section (e.g., "Data Management", "Indicators", "Strategies") is encapsulated within its own JavaScript module located in `frontend/js/modules/`. Shared functionalities like API call management, UI manipulation, and state management are abstracted into utility modules in `frontend/js/utils/`.

---

## Frontend-Backend Connection

The system employs a classic client-server architecture where the browser (client) runs the frontend, and `app.py` (server) provides the backend services.

### Backend Role (`app.py`)
- **API Provider**: Exposes all necessary endpoints (e.g., `/api/upload`, `/api/run-backtest`) for the frontend to function.
- **Static File Server**: `app.py` is configured to serve the static frontend files (HTML, CSS, JavaScript, images) located in the `frontend/` directory. `frontend/index.html` is typically served at the root URL (`/`), and other assets like CSS and JS are served from a `/static` path mapped to the `frontend/` directory.
- **Business Logic**: All core computations, data manipulations, and analysis happen on the backend.

### Frontend Role
- **User Interface**: Presents the UI to the user, allowing interaction with the system's features.
- **API Consumer**: Initiates requests to the backend API endpoints based on user actions.
- **Dynamic Updates**: Processes responses from the backend to dynamically update the UI without full page reloads (e.g., displaying data previews, charts, backtest results).

---

## Key Files & Their Roles

### 1. `frontend/index.html`
- **The Single Page**: This is the main and only HTML file served to the browser. It defines the overall page structure, including:
    - The persistent sidebar for navigation.
    - The main content area where different "sections" or "tabs" are dynamically shown or hidden.
    - All static UI elements, forms, buttons, and placeholders for dynamic content for every feature.
- **Loads Core Assets**: Includes CSS (Bootstrap, custom styles from `frontend/css/style.css`), JavaScript libraries (Chart.js), and the main application script (`/static/js/main.js` as an ES6 module).
- **Defines UI Sections**: Contains distinct `div` elements (e.g., `<div id="data-section" class="content-section">...</div>`) for each tab in the application (Data, Indicators, Strategies, etc.).

### 2. `frontend/js/main.js`
- **Frontend Orchestrator**: This is the central entry point and controller for all frontend JavaScript logic.
- **Initializes Application**: Sets up tab navigation, event listeners, and initializes all feature-specific modules.
- **Manages Navigation**: Controls which UI section is visible based on user clicks on sidebar tabs or the URL hash. It ensures that users can only navigate to sections if prerequisite conditions are met (e.g., data must be uploaded and processed before accessing strategy backtesting).
- **Module Coordination**: Imports and calls functions from the various modules in `frontend/js/modules/` and `frontend/js/utils/`.
- **Global Event Handling**: Can listen for and dispatch global custom events for inter-module communication if needed.

### 3. `app.py` (Backend Interaction Context)
- While a backend file, its role is crucial for the frontend's existence. It:
    - Serves `frontend/index.html` at the application's root URL.
    - Serves all files under `frontend/` (like JS, CSS) via a static file configuration (e.g., `/static` mapped to the `frontend` directory).
    - Defines all `/api/*` endpoints that `frontend/js/utils/api.js` (and by extension, the feature modules) will call.

### 4. `frontend/index.html`: Defines the indicators form with collapsible groups and select all/group checkboxes for indicator selection.
- **Indicators Panel UI Improvements (2024-06-09)**:
  - The indicators form in the Indicators tab now features:
    - A "Select All" checkbox to select/deselect all indicators at once.
    - Each indicator group (e.g., Moving Averages, Momentum, Volatility, etc.) is now a collapsible Bootstrap card for better organization and navigation.
    - Each group has its own group select checkbox to select/deselect all indicators in that group.
    - All checkboxes are synchronized: selecting/deselecting at any level updates group and global states (including indeterminate state for partial selection).
    - Candlestick pattern checkboxes are also grouped and can be toggled together.
  - These changes improve usability, especially when working with many indicators.

### 5. `frontend/js/modules/indicatorPanel.js`: Handles all indicator form logic, including select all/group checkboxes, collapsible groups, and indicator state management.

---

## UI Structure & Navigation

### Tabbed Interface
- The UI is organized into a series of tabs accessible via the sidebar (defined in `frontend/index.html`).
- Each tab corresponds to a major workflow step or feature set (e.g., Data, Indicators, Strategy & Backtest, Optimization, Seasonality, Results).
- Clicking a tab updates the main content area to show the relevant section. The "Strategies" and "Backtest" tabs have been merged into a single "Strategy & Backtest" tab. This tab allows users to select a strategy, configure its parameters, set up backtesting parameters (initial capital, commission, date range), run the backtest, and view its results, all in one integrated section.

### Dynamic Content Loading
- **Section Visibility**: `frontend/js/main.js` manages the visibility of these sections. When a tab is clicked:
    1.  The previously active section is hidden.
    2.  The target section (e.g., `div#data-section`) corresponding to the clicked tab is displayed.
    3.  The URL hash is updated (e.g., `myapp.com/#data-section`) to reflect the current view, allowing for bookmarking and direct navigation.
- **Conditional Navigation**: `main.js` includes logic (in `canActivateTab`) to prevent navigation to certain tabs if prerequisites are not met (e.g., data must be loaded and processed before the "Strategy & Backtest" or "Indicators" tabs can be accessed). This relies on the `appState`.
- **Page Title**: The main page title (H1 tag) is dynamically updated to reflect the currently active tab/section.

---

## JavaScript Module System

The frontend leverages ES6 modules for better organization, maintainability, and reusability.

### Core Modules (`frontend/js/modules/`)
Each file in this directory typically manages a specific section of the `frontend/index.html` and its associated functionality:
- `dataManager.js`: Handles CSV file upload, interaction with the "Arrange Data" feature, data processing requests, and displaying data previews/summaries in the "Data" section.
- `indicatorPanel.js`: Manages the "Indicators" section, allowing users to select indicators, configure their parameters, send requests to add them to the processed data, and trigger chart plotting.
- `strategySelector.js`: Populates strategy choices in relevant dropdowns, displays descriptions, and handles parameter configuration for selected strategies in the "Strategy & Backtest" section. It works in conjunction with `backtestView.js` for the backtesting part of this combined section.
- `backtestView.js`: Manages the backtesting functionality within the "Strategy & Backtest" section. This includes handling inputs for backtest settings (initial capital, commission, date range), initiating backtest runs via API calls (using strategy configurations provided via `appState` by `strategySelector.js`), and displaying performance metrics and equity curve charts in the designated areas within the "Strategy & Backtest" tab. Its initialization is still handled in `main.js`, and it operates on the DOM elements now part of the `#strategies-section`.
- `optimizationPanel.js`: Handles the "Optimization" section, allowing users to configure strategy parameter optimization, run optimization tasks, and view results.
- `seasonalityAnalyzer.js`: Manages the "Seasonality" section, enabling various seasonality analyses and displaying their corresponding charts and data.
- `resultsViewer.js`: Aggregates and displays detailed results, performance metrics, and trade history, typically in the "Results" section.
- `configManager.js`: Manages saving and loading of user configurations (e.g., strategy settings, indicator choices).

### Utility Modules (`frontend/js/utils/`)
These modules provide shared, reusable functionality across the different feature modules:
- `api.js`: **Crucial for backend interaction.** Centralizes all `fetch` calls to the backend API endpoints defined in `app.py`. It provides named functions for each API call (e.g., `uploadData()`, `runBacktest()`), handling request formatting and basic response parsing/error checking. This abstraction makes feature modules cleaner and API management easier.
- `state.js`: Defines and manages the global frontend application state (`appState`). This object tracks key information like whether data has been uploaded/processed, the available date range, selected strategies, current configuration, etc. It often uses `sessionStorage` to persist state across page reloads within the same session.
- `ui.js`: Contains helper functions for common UI manipulations, such as showing/hiding elements, displaying error messages or notifications (often using the modals defined in `index.html`), managing loading spinners, and activating/deactivating tabs.
- `formatters.js`: Provides functions for formatting data for display (e.g., dates, numbers, percentages).
- `strategies-config.js` (if present, or similar): Might hold static configuration or metadata about available strategies if not fully dynamic from the backend.

---

## State Management (`appState`)

- **Central State Object**: `frontend/js/utils/state.js` exports an `appState` object (or a class to manage it). This object serves as the single source of truth for shared frontend application state.
- **Key Information Tracked**:
    - `dataUploaded` (boolean): True if a data file has been successfully uploaded.
    - `dataProcessed` (boolean): True if the uploaded data has been cleaned and processed by the backend.
    - `dateRange` (object): Contains `startDate` and `endDate` available from the processed data.
    - `availableIndicators` (array): List of indicators currently calculated on the `PROCESSED_DATA`.
    - `availableStrategies` (array): List of strategies fetched from the backend.
    - `currentStrategyConfig` (object): Parameters for the currently selected strategy.
    - `activeTab` (string): The ID of the currently active UI section (e.g., `#data-section`).
    - Other states relevant to ongoing operations like optimization status.
- **Persistence**: The state is typically persisted in the browser's `sessionStorage`. This allows the application to remember its state if the user reloads the page, but the state is cleared when the browser tab is closed.
- **Access and Modification**: Modules import `appState` to read current state. They update the state by calling specific setter functions (if provided by `state.js`) or by directly modifying its properties (less ideal but possible). Changes to `appState` often trigger UI updates or enable/disable functionality elsewhere.
- **Initialization**: On application load (`main.js`), the state is initialized, often by trying to load any persisted state from `sessionStorage`.

---

## API Communication (`utils/api.js`)

- **Centralized API Logic**: All communication with the backend API (defined in `app.py`) is funneled through `frontend/js/utils/api.js`. This module typically exports a set of asynchronous functions, each corresponding to a specific backend endpoint.
- **Fetch API**: These functions use the browser's `fetch` API to make HTTP requests (GET, POST, etc.).
- **Request/Response Handling**:
    - **Request Payload**: Functions in `api.js` handle the construction of request bodies (e.g., JSON payloads for POST requests, FormData for file uploads).
    - **Response Parsing**: They parse responses from the backend (e.g., converting JSON responses to JavaScript objects, handling base64 image data).
    - **Error Handling**: Basic error handling is implemented (e.g., checking response status codes, catching network errors). More specific error handling might be delegated to the calling module or handled via global error display mechanisms managed by `ui.js`.
- **Example Functions**:
    - `async function uploadData(file) { /* ... */ }`
    - `async function addIndicators(indicatorConfig) { /* ... */ }`
    - `async function runBacktest(strategyConfig, backtestConfig) { /* ... */ }`
- **Benefits**:
    - **Decoupling**: Feature modules (`frontend/js/modules/`) are decoupled from the specifics of API calls.
    - **Maintainability**: If an API endpoint changes, updates are primarily localized to `api.js`.
    - **Consistency**: Ensures API calls are made consistently across the application.

---

## How to Extend or Modify

### 1. **Adding a New UI Section/Feature**
1.  **HTML (`frontend/index.html`):**
    *   Add a new list item (`<li>`) to the sidebar navigation.
    *   Add a new `div` with class `content-section` and a unique `id` in the main content area. Populate this `div` with the necessary HTML structure (forms, placeholders for results, etc.) for your new feature. Note: If adding features related to strategy configuration or backtesting, consider if they fit within the existing "Strategy & Backtest" tab.
2.  **JavaScript Module (`frontend/js/modules/`):**
    *   Create a new `.js` file (e.g., `newFeatureManager.js`).
    *   Implement the logic for your feature in this module: event listeners for inputs, functions to gather data from the form, etc.
    *   If it interacts with the backend, add necessary functions to `frontend/js/utils/api.js` and call them from your new module.
    *   Update `appState` in `frontend/js/utils/state.js` if your feature introduces new shared state.
3.  **Main Orchestrator (`frontend/js/main.js`):**
    *   Import your new module.
    *   Call its initialization function within `initializeApp()`.
    *   Ensure the new tab is handled correctly in `initializeTabNavigation` and `canActivateTab` (if it has prerequisites).
4.  **CSS (`frontend/css/style.css`):**
    *   Add any custom styles for your new section if Bootstrap doesn't cover it.
5.  **Documentation:** **Update this `README_frontend.md` file** to include the new section, its module, and its purpose.

### 2. **Modifying Existing Features or Parameters**
1.  **HTML (`frontend/index.html`):**
    *   Locate the relevant section (e.g., `#strategies-section` for strategy and backtesting features) and modify its HTML.
2.  **JavaScript Module (`frontend/js/modules/`):**
    *   Identify the module responsible for the feature.
    *   Update its JavaScript to handle the new/changed input fields, modify how data is processed or sent to the API, or change how results are displayed.
3.  **API Utility (`frontend/js/utils/api.js`):**
    *   If backend API parameters change, update the corresponding function in `api.js`.
4.  **State (`frontend/js/utils/state.js`):**
    *   If the change affects global state, update `appState` and its management logic.
5.  **Backend (`app.py`):**
    *   Coordinate with backend changes if the API endpoint signature or behavior is modified.
6.  **Documentation:** **Update this `README_frontend.md` file** detailing the changes.

### 3. **Updating API Interactions**
1.  **Backend (`app.py`):** First, understand or implement the changes in the backend API endpoint (URL, method, request body, response structure).
2.  **API Utility (`frontend/js/utils/api.js`):**
    *   Modify the existing function or add a new one to match the updated backend endpoint. Adjust how the request is made and how the response is processed.
3.  **Calling Module (`frontend/js/modules/`):**
    *   Update the feature module that calls this API function to provide the correct parameters and handle the (potentially new) response structure.
4.  **Documentation:** **Update this `README_frontend.md` file**, especially the "API Communication" section if the general pattern changes, or the relevant module's description.

### 4. **Indicators Panel UI**: To add new indicator groups or checkboxes, update `frontend/index.html` (form structure) and ensure the new checkboxes have a group class (e.g., `momentum-checkbox`). Update `frontend/js/modules/indicatorPanel.js` if new group logic is needed. Checkbox state logic is handled automatically for any group with the `.group-select` and `data-group` attributes.

---

## Testing & Debugging

- **Browser Developer Tools**: Essential for frontend development.
    - **Console**: Check for JavaScript errors, log messages from `AppLogger` and `console.log`. Inspect `appState` by typing `appState` (or its exported name) if it's globally accessible or exposed for debugging.
    - **Network Tab**: Monitor API requests to `app.py`. Check request URLs, methods, payloads, and response status codes and content. This is vital for diagnosing frontend-backend communication issues.
    - **Elements/Inspector Tab**: Inspect the DOM structure, check CSS styles, and see how elements are being manipulated by JavaScript.
    - **Sources Tab**: Debug JavaScript by setting breakpoints, stepping through code, and inspecting variables.
- **Manual Testing**: Thoroughly test all UI interactions in the modified section and related workflows.
    - Test different inputs and edge cases.
    - Ensure conditional logic (like tab enabling/disabling) works correctly based on `appState`.
- **Frontend Logger (`AppLogger`)**:
    - `frontend/index.html` includes a custom `AppLogger` script. Use `AppLogger.debug()`, `AppLogger.info()`, `AppLogger.warning()`, `AppLogger.error()`, `AppLogger.api()`, and `AppLogger.perf()` for structured and filterable logging in the browser console. This is more organized than scattered `console.log` statements.
- **Error Modals**: The application should display user-friendly error messages (often via Bootstrap modals triggered by `ui.js` helpers) when API calls fail or other issues occur. Verify these are working.
- **Hot Reloading (if set up)**: If your development environment supports hot reloading, frontend changes (HTML, CSS, JS) should reflect in the browser automatically, speeding up development.
- **Troubleshooting Common Issues**:
    - *Tab not activating/UI not updating*: Check `appState` conditions in `main.js` (`canActivateTab`), JavaScript errors in the console, and ensure event listeners are correctly attached.
    - *API calls failing*: Check the Network tab for request/response details. Verify endpoint URLs, request methods, and payload structures against `app.py`. Check backend server logs.
    - *Charts not rendering*: Ensure Chart.js is loaded, the canvas element exists, and the data passed to Chart.js is in the correct format. Look for console errors.

---

## Best Practices

- **Keep modules focused and SRP (Single Responsibility Principle)**: Each module should ideally handle one major feature or section.
- **Use utility functions**: Abstract repeated logic (API calls, common UI updates, data formatting) into `frontend/js/utils/` modules.
- **Consistent Naming**: Use clear, descriptive, and consistent names for variables, functions, DOM IDs, and CSS classes.
- **Comment Non-Obvious Code**: Explain complex logic, workarounds, or important decisions in comments.
- **Accessibility (A11Y)**:
    - Use semantic HTML.
    - Ensure all form inputs have associated labels (or `aria-label`, `title` for accessibility).
    - Ensure interactive elements are keyboard navigable and focusable.
    - Test with accessibility tools if possible.
- **Modern JavaScript (ES6+)**: Use `const` and `let` instead of `var`. Utilize features like arrow functions, template literals, and destructuring where appropriate.
- **Graceful Error Handling**: Always anticipate and handle potential errors from API calls, user input, or unexpected states. Display clear messages to the user.
- **Performance**: Be mindful of performance, especially when dealing with large datasets or frequent DOM manipulations. Debounce event listeners where necessary.

---

## Contributing & Coordination

- **Understand Existing Code**: Before making changes, take time to understand the relevant modules and how they fit into the overall architecture.
- **Backend Coordination**: If your changes require modifications to API endpoints (new ones, changed parameters, different responses), communicate clearly with backend developers. Ensure `app.py` and `frontend/js/utils/api.js` are synchronized.
- **Testing**: After making changes, thoroughly test the affected functionality and ideally, perform a quick run-through of related workflows to catch any unintended side effects.
- **Pull Requests (if applicable)**: In your pull request description, clearly summarize the changes made, which files/modules were affected, any new parameters or API endpoints introduced, and why the change was necessary.
- **Changelog**: Follow the "Changelog Template" section below to document your changes.
- **Documentation (This File!)**: **Crucially, update this `README_frontend.md` file** to reflect any structural changes, new modules, modified workflows, or significant parameter alterations.

---

## Glossary

- **SPA (Single-Page Application)**: The frontend operates as a single HTML page (`index.html`) where content is dynamically updated by JavaScript.
- **Module (`.js` file)**: Typically refers to a JavaScript file in `frontend/js/modules/` or `frontend/js/utils/` that encapsulates a specific piece of functionality.
- **`appState`**: The central JavaScript object (from `frontend/js/utils/state.js`) holding the frontend's global state.
- **API Endpoint**: A specific URL on the backend (`app.py`) that the frontend calls to perform an action or retrieve data (e.g., `/api/process-data`).
- **Content Section**: A `div` element within `frontend/index.html` (e.g., `<div id="data-section" class="content-section">`) that corresponds to a major feature or tab in the UI.
- **Tab**: A navigation item in the sidebar of `frontend/index.html` used to switch between different content sections.
- **`sessionStorage`**: Browser storage mechanism used by `appState` to persist data for the duration of a user's session.
- **Chart.js**: A JavaScript library used for rendering interactive charts in the UI.
- **Bootstrap**: A CSS framework used for responsive layout and pre-styled UI components.
- **`AppLogger`**: The custom logging utility defined in `index.html` for structured console messages.

---

## **Update Policy (Mandatory)**

**Any developer making changes to the frontend MUST update this file (`README_frontend.md`) if those changes affect:**

1.  **File Structure or Key Roles:**
    *   Adding, removing, or significantly renaming files in `frontend/js/modules/` or `frontend/js/utils/`.
    *   Changing the fundamental role of `frontend/index.html` or `frontend/js/main.js`.
2.  **UI Structure & Navigation:**
    *   Adding or removing main UI sections/tabs from `frontend/index.html`.
    *   Altering the core navigation logic in `frontend/js/main.js`.
3.  **JavaScript Module System:**
    *   Changing how modules are loaded, initialized, or interact.
4.  **State Management:**
    *   Modifying the structure of `appState` in `frontend/js/utils/state.js`.
    *   Changing how state is persisted or accessed.
5.  **API Communication:**
    *   Adding new functions to `frontend/js/utils/api.js` for new backend endpoints.
    *   Significantly changing the parameters or response handling for existing API utility functions.
    *   Altering the general pattern of frontend-backend communication.
6.  **Workflow Logic:**
    *   Changing the sequence of operations for a feature.
    *   Modifying prerequisites for accessing certain UI sections (e.g., changes to `canActivateTab` logic in `main.js`).
7.  **Build Process or Dependencies (if applicable in the future):**
    *   Introducing new libraries or tools that affect how the frontend is built or run.

**When updating, ensure you describe:**
- **What** was changed.
- **Why** it was changed.
- **How** it impacts other parts of the frontend or developers working on it.
- **Which files/modules** were affected.
- Any new parameters, API endpoints, UI elements, or state variables introduced.
- Migration or update instructions for other developers if the change is breaking or requires specific actions.

**Failure to keep this document updated will lead to inconsistencies, increase onboarding time for new developers, and hinder effective collaboration, especially with AI-assisted development.**

---

## Changelog Template

> **[LATEST_DATE] [AI Assistant - Gemini]**
> - **Summary**: Merged the "Strategies" and "Backtest" tabs into a single "Strategy & Backtest" tab. This consolidates strategy selection, parameter configuration, backtest setup, execution, and results viewing into one streamlined workflow.
> - **Affected Files/Modules**:
>   - `frontend/index.html`: Removed "Backtest" tab from sidebar, renamed "Strategies" tab, and merged HTML content of backtest section into strategy section. Adjusted element IDs for consistency.
>   - `frontend/js/main.js`: Removed DOM reference to the old `backtest-tab`. Tab navigation logic now handles the merged tab. `initializeBacktestView()` is still called.
>   - `frontend/js/modules/strategySelector.js`: Continues to manage strategy selection and parameterization. Implicitly works with `backtestView.js` via `appState` for providing strategy details to the backtest.
>   - `frontend/js/modules/backtestView.js`: Continues to manage backtest execution and results display, now operating on DOM elements within the merged `#strategies-section`. Relies on `appState` for strategy details.
> - **New UI Elements/Parameters**: The UI elements for backtesting are now part of the "Strategy & Backtest" tab. No new parameters, but existing ones are relocated.
> - **Notes/Instructions**: The primary interaction for strategy definition and testing now occurs within the "Strategy & Backtest" tab.

---

## Deprecated/Legacy Files

- The following files are no longer used in the current frontend architecture and MUST NOT be modified:
  - `frontend/js/app.js`

All new or updated logic must be implemented in the files and modules described in the 'Key Files & Their Roles' section above.

---

## LLM/AI Contributor Rule

- Before making any code changes, always:
  1. Check which JS files are loaded in `frontend/index.html` (look for `<script src=...>`).
  2. Confirm the file/module is referenced in the documentation and is part of the current architecture.
  3. If in doubt, ask for clarification or consult the documentation.

---

## Additional Notes

- **Frontend and backend must remain in sync.** If you change the workflow or data format, coordinate with backend maintainers.
- **For LLM/AI contributors:** Refer to the main project `readmeLLM.md` for overarching code patterns, architectural rules, and specific instructions related to AI-driven modifications. Adherence to the update policy in *this* document is critical for the LLM's understanding of the frontend.
- **For new developers:** Start by reading this file thoroughly. Then explore `frontend/js/main.js` to see how modules are initialized and navigate, followed by individual modules in `frontend/js/modules/` and utilities in `frontend/js/utils/` to understand specific features.
- **For troubleshooting:** Make extensive use of browser developer tools (Console, Network tab, Sources tab) and the `AppLogger`.
- **For accessibility:** Continuously strive to make the UI accessible. Test with keyboard navigation and, if possible, screen readers, especially after adding new interactive elements or forms.

--- 