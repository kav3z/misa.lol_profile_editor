/**
 * misa.lol Profile Editor Client-Side Controller
 * 
 * Manages:
 * - Real-time preview synchronization with safe plain-text rendering (preventing XSS).
 * - Client-side validation & live URL validity check (preventing invalid links from being clickable).
 * - Character counters for form inputs.
 * - AJAX PUT /api/profile with pending state & double-submission prevention.
 * - Field-level and global error presentation while preserving form entries on failure.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements: Form & Inputs
  const form = document.getElementById("profile-form");
  const displayNameInput = document.getElementById("displayName");
  const bioInput = document.getElementById("bio");
  const linkLabelInput = document.getElementById("linkLabel");
  const linkUrlInput = document.getElementById("linkUrl");
  const saveBtn = document.getElementById("save-btn");
  const saveBtnText = document.getElementById("save-btn-text");
  const saveSpinner = document.getElementById("save-spinner");
  const statusBanner = document.getElementById("status-banner");

  // DOM Elements: Character Counters
  const nameCount = document.getElementById("displayName-count");
  const bioCount = document.getElementById("bio-count");
  const linkLabelCount = document.getElementById("linkLabel-count");

  // DOM Elements: Live Preview
  const previewAvatar = document.getElementById("preview-avatar");
  const previewName = document.getElementById("preview-name");
  const previewBio = document.getElementById("preview-bio");
  const previewLinkAnchor = document.getElementById("preview-link-anchor");
  const previewLinkLabel = document.getElementById("preview-link-label");
  const previewLinkDisabled = document.getElementById("preview-link-disabled");
  const previewLinkDisabledLabel = document.getElementById("preview-link-disabled-label");

  // State
  let isSaving = false;
  let savedProfile = null;

  // Read initial profile data rendered by server
  try {
    const rawData = document.getElementById("initial-profile-data")?.textContent;
    if (rawData) {
      savedProfile = JSON.parse(rawData);
    }
  } catch (e) {
    console.error("Could not parse embedded profile data:", e);
  }

  // Fallback: If not embedded, fetch via GET /api/profile
  if (!savedProfile) {
    fetchProfileFromBackend();
  } else {
    syncPreview();
    updateCharCounters();
  }

  // ==========================================================================
  // URL VALIDATION LOGIC
  // ==========================================================================
  /**
   * Validates whether a URL meets the specification:
   * - Must be absolute https:// URL
   * - Must have a valid hostname
   * - Must reject http:, javascript:, data:, and malformed syntax
   */
  function isValidHttpsUrl(urlString) {
    const trimmed = (urlString || "").trim();
    if (!trimmed) return false;
    if (/\s/.test(trimmed)) return false;

    try {
      const parsed = new URL(trimmed);
      return parsed.protocol === "https:" && Boolean(parsed.hostname) && parsed.hostname.length > 0;
    } catch (_) {
      return false;
    }
  }

  // ==========================================================================
  // LIVE PREVIEW SYNCHRONIZATION
  // ==========================================================================
  /**
   * Updates the live preview card.
   * NOTE: All text values are assigned via .textContent to strictly treat
   * entered text as plain text and prevent HTML/XSS injection.
   */
  function syncPreview() {
    const rawName = displayNameInput.value;
    const rawBio = bioInput.value;
    const rawLabel = linkLabelInput.value;
    const rawUrl = linkUrlInput.value;

    const trimmedName = rawName.trim();
    const trimmedBio = rawBio.trim();
    const trimmedLabel = rawLabel.trim();
    const trimmedUrl = rawUrl.trim();

    // 1. Avatar (Initial of name or '?')
    previewAvatar.textContent = trimmedName ? trimmedName.charAt(0).toUpperCase() : "?";

    // 2. Display Name
    if (trimmedName) {
      previewName.textContent = rawName;
      previewName.classList.remove("empty-name");
    } else {
      previewName.textContent = "Untitled Profile";
      previewName.classList.add("empty-name");
    }

    // 3. Bio
    if (trimmedBio) {
      previewBio.textContent = rawBio;
      previewBio.classList.remove("empty-bio");
    } else {
      previewBio.textContent = "No bio provided.";
      previewBio.classList.add("empty-bio");
    }

    // 4. Link & URL Validation Check
    const effectiveLabel = trimmedLabel || "External link";
    const isUrlValid = isValidHttpsUrl(trimmedUrl);

    if (isUrlValid) {
      // Valid URL: show interactive, working link
      previewLinkLabel.textContent = effectiveLabel;
      previewLinkAnchor.href = trimmedUrl;
      previewLinkAnchor.classList.remove("hidden");
      previewLinkDisabled.classList.add("hidden");
    } else {
      // Invalid URL: MUST NOT become a clickable link in the preview
      previewLinkDisabledLabel.textContent = effectiveLabel;
      previewLinkAnchor.classList.add("hidden");
      previewLinkAnchor.removeAttribute("href");
      previewLinkDisabled.classList.remove("hidden");
    }
  }

  // ==========================================================================
  // CHARACTER COUNTERS & INPUT LISTENERS
  // ==========================================================================
  function updateCharCounters() {
    const nameLen = displayNameInput.value.trim().length;
    nameCount.textContent = `${nameLen} / 40`;
    nameCount.classList.toggle("limit-exceeded", nameLen > 40 || nameLen === 0);

    const bioLen = bioInput.value.trim().length;
    bioCount.textContent = `${bioLen} / 160`;
    bioCount.classList.toggle("limit-exceeded", bioLen > 160);

    const labelLen = linkLabelInput.value.trim().length;
    linkLabelCount.textContent = `${labelLen} / 30`;
    linkLabelCount.classList.toggle("limit-exceeded", labelLen > 30 || labelLen === 0);
  }

  // Wire real-time input event listeners
  [displayNameInput, bioInput, linkLabelInput, linkUrlInput].forEach(el => {
    el.addEventListener("input", () => {
      syncPreview();
      updateCharCounters();
      clearFieldError(el.id);
    });
  });

  // ==========================================================================
  // ERROR & STATUS DISPLAY HELPERS
  // ==========================================================================
  function showStatus(message, type = "success") {
    statusBanner.className = `status-banner ${type}`;
    statusBanner.textContent = message;
    statusBanner.classList.remove("hidden");
  }

  function hideStatus() {
    statusBanner.className = "status-banner hidden";
    statusBanner.textContent = "";
  }

  function setFieldError(fieldId, message) {
    const group = document.getElementById(`group-${fieldId}`);
    const errorEl = document.getElementById(`${fieldId}-error`);
    if (group && errorEl) {
      group.classList.add("has-error");
      errorEl.textContent = message;
    }
  }

  function clearFieldError(fieldId) {
    const group = document.getElementById(`group-${fieldId}`);
    const errorEl = document.getElementById(`${fieldId}-error`);
    if (group && errorEl) {
      group.classList.remove("has-error");
      errorEl.textContent = "";
    }
  }

  function clearAllErrors() {
    hideStatus();
    ["displayName", "bio", "linkLabel", "linkUrl"].forEach(clearFieldError);
  }

  // ==========================================================================
  // FORM SAVE / SUBMISSION (PUT /api/profile)
  // ==========================================================================
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (isSaving) return; // Prevent duplicate concurrent requests
    clearAllErrors();

    // Prepare payload
    const payload = {
      displayName: displayNameInput.value,
      bio: bioInput.value,
      link: {
        label: linkLabelInput.value,
        url: linkUrlInput.value
      }
    };

    // Client-side quick check
    let hasClientError = false;
    const trimmedName = payload.displayName.trim();
    const trimmedBio = payload.bio.trim();
    const trimmedLabel = payload.link.label.trim();
    const trimmedUrl = payload.link.url.trim();

    if (trimmedName.length < 1 || trimmedName.length > 40) {
      setFieldError("displayName", "Display name must be 1–40 characters after trimming.");
      hasClientError = true;
    }

    if (trimmedBio.length > 160) {
      setFieldError("bio", "Bio must not exceed 160 characters.");
      hasClientError = true;
    }

    if (trimmedLabel.length < 1 || trimmedLabel.length > 30) {
      setFieldError("linkLabel", "Link label must be 1–30 characters after trimming.");
      hasClientError = true;
    }

    if (!isValidHttpsUrl(trimmedUrl)) {
      setFieldError("linkUrl", "Link URL must be a valid absolute https:// URL with a hostname.");
      hasClientError = true;
    }

    if (hasClientError) {
      showStatus("Please fix the highlighted errors before saving.", "error");
      return;
    }

    // Set saving state: disable button, show spinner
    setSavingState(true);

    try {
      const response = await fetch("/api/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        // SUCCESS: Update saved profile reference and notify user
        savedProfile = data;
        
        // Re-populate inputs with sanitized server values
        displayNameInput.value = data.displayName;
        bioInput.value = data.bio;
        linkLabelInput.value = data.link.label;
        linkUrlInput.value = data.link.url;

        syncPreview();
        updateCharCounters();
        showStatus("Profile saved successfully!", "success");
      } else {
        // SERVER VALIDATION ERROR (HTTP 400 or other)
        // Keep entered values intact!
        handleServerError(data);
      }
    } catch (err) {
      // Network or unexpected failure
      console.error("Save request failed:", err);
      showStatus("Network error: Could not reach the server. Please check your connection and try again.", "error");
    } finally {
      setSavingState(false);
    }
  });

  function setSavingState(saving) {
    isSaving = saving;
    saveBtn.disabled = saving;
    if (saving) {
      saveSpinner.classList.remove("hidden");
      saveBtnText.textContent = "Saving...";
    } else {
      saveSpinner.classList.add("hidden");
      saveBtnText.textContent = "Save Profile";
    }
  }

  function handleServerError(data) {
    const generalMsg = data.message || data.error || "Failed to save profile. Please correct the errors.";
    showStatus(generalMsg, "error");

    if (Array.isArray(data.details)) {
      data.details.forEach(item => {
        // Map backend field names to DOM input IDs
        if (item.field === "displayName") {
          setFieldError("displayName", item.message);
        } else if (item.field === "bio") {
          setFieldError("bio", item.message);
        } else if (item.field === "link.label" || item.field === "label") {
          setFieldError("linkLabel", item.message);
        } else if (item.field === "link.url" || item.field === "url") {
          setFieldError("linkUrl", item.message);
        }
      });
    }
  }

  // ==========================================================================
  // INITIAL FETCH FALLBACK
  // ==========================================================================
  async function fetchProfileFromBackend() {
    try {
      const response = await fetch("/api/profile");
      if (!response.ok) throw new Error("Failed to load profile");
      const data = await response.json();
      savedProfile = data;

      displayNameInput.value = data.displayName || "";
      bioInput.value = data.bio || "";
      linkLabelInput.value = data.link?.label || "";
      linkUrlInput.value = data.link?.url || "";

      syncPreview();
      updateCharCounters();
    } catch (err) {
      console.error("Failed to load profile:", err);
      showStatus("Could not load saved profile from server.", "error");
    }
  }
});
