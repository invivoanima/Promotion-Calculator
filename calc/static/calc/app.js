document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.querySelector("#sidebar");
  const menuButton = document.querySelector("[data-menu-toggle]");
  if (sidebar && menuButton) {
    menuButton.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (event) => {
      if (window.innerWidth <= 820 && sidebar.classList.contains("open") && !sidebar.contains(event.target) && !menuButton.contains(event.target)) {
        sidebar.classList.remove("open");
      }
    });
  }

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  const recordForm = document.querySelector("[data-record-form]");
  if (recordForm) {
    let dirty = false;
    recordForm.addEventListener("input", () => { dirty = true; });
    recordForm.addEventListener("submit", () => { dirty = false; });
    window.addEventListener("beforeunload", (event) => {
      if (!dirty) return;
      event.preventDefault();
      event.returnValue = "";
    });
  }

  const focusButton = document.querySelector("[data-form-focus]");
  if (focusButton) {
    focusButton.addEventListener("click", () => {
      document.querySelector("#record-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
      document.querySelector("#record-form input:not([type=hidden]), #record-form select")?.focus({ preventScroll: true });
    });
  }

  const methodForm = document.querySelector("[data-method-form]");
  if (methodForm) {
    const select = methodForm.querySelector("select[name=method]");
    const sections = methodForm.querySelectorAll("[data-method]");
    const updateSections = () => sections.forEach((section) => {
      section.hidden = select.value !== section.dataset.method;
    });
    select?.addEventListener("change", updateSections);
    updateSections();
  }

  document.querySelectorAll(".message").forEach((message) => {
    window.setTimeout(() => message.remove(), 4500);
  });

  const guestRoot = document.querySelector("[data-guest-calculator]");
  if (guestRoot) {
    const storageKey = guestRoot.dataset.guestLocalKey;

    const readGuestState = () => {
      try {
        const raw = window.localStorage.getItem(storageKey);
        const parsed = raw ? JSON.parse(raw) : {};
        return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
      } catch (error) {
        console.warn("비회원 계산값을 읽지 못했습니다.", error);
        return {};
      }
    };

    const writeGuestState = (state) => {
      window.localStorage.setItem(storageKey, JSON.stringify(state || {}));
    };

    const hasGuestRecords = (state) => Object.values(state).some(
      (entries) => Array.isArray(entries) && entries.length > 0,
    );

    const replaceDocument = (html) => {
      document.open();
      document.write(html);
      document.close();
    };

    const submitGuestState = async (form) => {
      const formData = new FormData(form);
      formData.set("guest_payload", JSON.stringify(readGuestState()));
      const response = await window.fetch(form.getAttribute("action") || window.location.href, {
        method: "POST",
        body: formData,
        credentials: "same-origin",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "계산값을 처리하지 못했습니다.");
        writeGuestState(result.storage);
        window.location.assign(result.redirect_url);
        return;
      }
      const html = await response.text();
      if (!response.ok) throw new Error("계산 화면을 불러오지 못했습니다.");
      replaceDocument(html);
    };

    document.querySelectorAll("form[data-guest-state-form]").forEach((form) => {
      form.addEventListener("submit", async (event) => {
        if (event.defaultPrevented) return;
        event.preventDefault();
        try {
          await submitGuestState(form);
        } catch (error) {
          console.error(error);
          window.alert("계산값을 처리하지 못했습니다. 잠시 후 다시 시도해주세요.");
        }
      });
    });

    const resetButton = document.querySelector("[data-guest-reset]");
    resetButton?.addEventListener("click", () => {
      if (!window.confirm("이 브라우저에 저장된 계산값을 모두 삭제할까요?")) return;
      window.localStorage.removeItem(storageKey);
      window.location.assign(resetButton.dataset.resetUrl);
    });

    const hydrateForm = document.querySelector("form[data-guest-hydrate]");
    const currentState = readGuestState();
    if (hydrateForm && guestRoot.dataset.guestHydrated !== "true" && hasGuestRecords(currentState)) {
      submitGuestState(hydrateForm).catch((error) => {
        console.error(error);
        window.alert("이 브라우저에 저장된 계산값을 불러오지 못했습니다.");
      });
    }
  }
});
