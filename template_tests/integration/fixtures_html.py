from __future__ import annotations

FORM_WORKFLOW_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Workflow Fixture</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; }
      .hidden { display: none; }
    </style>
  </head>
  <body>
    <h1>Demo Form</h1>

    <form id="demo-form">
      <label for="full-name">Full name</label>
      <input id="full-name" type="text" />

      <label for="role">Role</label>
      <select id="role">
        <option value="">Select one</option>
        <option value="qa">QA Engineer</option>
        <option value="sdet">SDET</option>
      </select>

      <label>
        <input id="agree" type="checkbox" />
        I agree to continue
      </label>

      <button id="submit-btn" type="button">Submit</button>
    </form>

    <section id="result" class="hidden" aria-live="polite">
      <p id="status"></p>
      <p id="submitted-name"></p>
      <p id="submitted-role"></p>
      <p id="submitted-agreement"></p>
    </section>

    <script>
      document.getElementById("submit-btn").addEventListener("click", () => {
        const name = document.getElementById("full-name").value;
        const role = document.getElementById("role").value;
        const agreed = document.getElementById("agree").checked;

        document.getElementById("status").textContent = "Submission complete";
        document.getElementById("submitted-name").textContent = `Name: ${name}`;
        document.getElementById("submitted-role").textContent = `Role: ${role}`;
        document.getElementById("submitted-agreement").textContent =
          `Agreed: ${agreed ? "yes" : "no"}`;
        document.getElementById("result").classList.remove("hidden");
      });
    </script>
  </body>
</html>
"""


A11Y_INACCESSIBLE_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Inaccessible Fixture</title>
  </head>
  <body>
    <h1>Broken Form</h1>
    <input id="email" type="email" />
    <button id="submit-btn" type="button">Send</button>
  </body>
</html>
"""


A11Y_ACCESSIBLE_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Accessible Fixture</title>
  </head>
  <body>
    <main>
      <h1>Fixed Form</h1>
      <label for="email">Email address</label>
      <input id="email" type="email" />
      <button id="submit-btn" type="button">Send</button>
    </main>
  </body>
</html>
"""


SUBPROCESS_PASSING_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Passing Fixture</title>
  </head>
  <body>
    <h1 id="page-title">Passing Page</h1>
    <p id="summary">This page is used for artifact lifecycle tests.</p>
  </body>
</html>
"""


SUBPROCESS_FAILING_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Failing Fixture</title>
  </head>
  <body>
    <h1 id="page-title">Expected Heading</h1>
    <p id="summary">This page is used for failure artifact tests.</p>
  </body>
</html>
"""

BROKEN_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Accessibility Violation Fixture</title>
  </head>
  <body>
    <!-- Missing label for input triggers a11y violation -->
    <input id="email" type="email" />
    <button type="submit">Send</button>
  </body>
</html>
"""

SIMPLE_PAGE_HTML = """
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <title>Accessible Fixture</title>
          </head>
          <body>
            <label for="name-input">Name</label>
            <input id="name-input" type="text" />
            <button type="button">Submit</button>
          </body>
        </html>
        """

FORM_WORKFLOW_HTML_NAME = "form_workflow.html"
A11Y_INACCESSIBLE_HTML_NAME = "form_inaccessible.html"
A11Y_ACCESSIBLE_HTML_NAME = "form_accessible.html"
SUBPROCESS_PASSING_HTML_NAME = "subprocess_passing.html"
SUBPROCESS_FAILING_HTML_NAME = "subprocess_failing.html"
BROKEN_PAGE_HTML_NAME = "broken_page.html"
SIMPLE_PAGE_HTML_NAME = "simple_page.html"
