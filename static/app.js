function debounce(fn, delay) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

document.addEventListener("DOMContentLoaded", () => {
  const tripList = document.getElementById("trip-list");
  const input = document.getElementById("destination-input");
  const suggestionsContainer = document.getElementById("destination-suggestions");

  if (tripList) {
    console.log("Planificador de viajes inicializado. Viajes actuales:");
    const cards = tripList.querySelectorAll(".trip-card");
    cards.forEach((card) => {
      const destination = card.querySelector(".trip-title")?.textContent?.trim();
      const days = card.querySelector(".trip-days")?.textContent?.trim();
      console.log(`- ${destination} (${days})`);
    });
  } else {
    console.log("No hay viajes para mostrar todavía.");
  }

  if (!input || !suggestionsContainer) {
    return;
  }

  let lastQuery = "";
  let currentSuggestions = [];
  let highlightedIndex = -1;

  function clearSuggestions() {
    suggestionsContainer.innerHTML = "";
    suggestionsContainer.hidden = true;
    currentSuggestions = [];
    highlightedIndex = -1;
  }

  function renderSuggestions(suggestions) {
    suggestionsContainer.innerHTML = "";

    if (!suggestions.length) {
      const emptyEl = document.createElement("div");
      emptyEl.className = "suggestions-empty";
      emptyEl.textContent = "No se encontraron coincidencias.";
      suggestionsContainer.appendChild(emptyEl);
      suggestionsContainer.hidden = false;
      currentSuggestions = [];
      highlightedIndex = -1;
      return;
    }

    currentSuggestions = suggestions;
    highlightedIndex = -1;

    suggestions.forEach((suggestion, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "suggestion-item";
      button.setAttribute("data-index", String(index));
      button.setAttribute("aria-selected", "false");

      const mainSpan = document.createElement("span");
      mainSpan.className = "suggestion-main";
      mainSpan.textContent = suggestion.city;

      const secondarySpan = document.createElement("span");
      secondarySpan.className = "suggestion-secondary";
      secondarySpan.textContent = suggestion.country;

      button.appendChild(mainSpan);
      button.appendChild(secondarySpan);

      button.addEventListener("mousedown", (event) => {
        event.preventDefault();
        chooseSuggestion(index);
      });

      suggestionsContainer.appendChild(button);
    });

    suggestionsContainer.hidden = false;
  }

  function chooseSuggestion(index) {
    const suggestion = currentSuggestions[index];
    if (!suggestion) return;

    input.value = suggestion.label || `${suggestion.city}, ${suggestion.country}`;
    clearSuggestions();
  }

  function updateHighlight(newIndex) {
    const items = suggestionsContainer.querySelectorAll(".suggestion-item");
    items.forEach((item, idx) => {
      const isSelected = idx === newIndex;
      item.setAttribute("aria-selected", isSelected ? "true" : "false");
    });
    highlightedIndex = newIndex;
  }

  const fetchSuggestions = debounce(async (value) => {
    const query = value.trim();
    if (query.length < 2) {
      clearSuggestions();
      return;
    }

    lastQuery = query;

    try {
      const response = await fetch(`/api/cities?q=${encodeURIComponent(query)}`);
      if (!response.ok) {
        clearSuggestions();
        return;
      }
      const data = await response.json();

      if (input.value.trim() !== query) {
        return;
      }

      renderSuggestions(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("No se pudieron obtener sugerencias de destino", error);
      clearSuggestions();
    }
  }, 250);

  input.addEventListener("input", (event) => {
    const value = event.target.value || "";
    if (!value.trim()) {
      clearSuggestions();
      return;
    }
    fetchSuggestions(value);
  });

  input.addEventListener("keydown", (event) => {
    if (suggestionsContainer.hidden) return;

    const items = suggestionsContainer.querySelectorAll(".suggestion-item");
    if (!items.length) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      const nextIndex = highlightedIndex < items.length - 1 ? highlightedIndex + 1 : 0;
      updateHighlight(nextIndex);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      const prevIndex = highlightedIndex > 0 ? highlightedIndex - 1 : items.length - 1;
      updateHighlight(prevIndex);
    } else if (event.key === "Enter") {
      if (highlightedIndex >= 0) {
        event.preventDefault();
        chooseSuggestion(highlightedIndex);
      } else if (currentSuggestions.length === 1) {
        event.preventDefault();
        chooseSuggestion(0);
      }
    } else if (event.key === "Escape") {
      clearSuggestions();
    }
  });

  input.addEventListener("blur", () => {
    setTimeout(() => {
      clearSuggestions();
    }, 120);
  });
});
