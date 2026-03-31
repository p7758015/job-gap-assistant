async function analyzeJob(payload) {
  const response = await fetch("/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message =
      response.status === 0
        ? "Сервер не отвечает."
        : `Ошибка API (${response.status}).`;
    throw new Error(message);
  }

  return response.json();
}

function setupForm() {
  const form = document.getElementById("analyze-form");
  const button = document.getElementById("analyze-button");
  const loadingEl = document.getElementById("loading-indicator");
  const errorEl = document.getElementById("form-error");
  const jobField = document.getElementById("job_description");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorEl.classList.add("hidden");
    errorEl.textContent = "";

    const jobDescription = jobField.value.trim();
    const candidateProfile = document
      .getElementById("candidate_profile")
      .value.trim();

    // Простая валидация
    jobField.classList.remove("field-error");
    const hint = document.getElementById("job_description_hint");
    hint.textContent =
      "Обязательное поле. Чем детальнее описание, тем точнее анализ.";
    hint.style.color = "#6b7280";

    if (!jobDescription) {
      jobField.classList.add("field-error");
      hint.textContent = "Добавь текст вакансии.";
      hint.style.color = "#b91c1c";
      return;
    }

    // UI: loading state
    button.disabled = true;
    loadingEl.classList.remove("hidden");

    try {
      const payload = {
        job_description: jobDescription,
        candidate_profile: candidateProfile || null,
      };

      const data = await analyzeJob(payload);
      renderResults(data);
    } catch (err) {
      console.error(err);
      errorEl.textContent =
        "Не удалось получить ответ от сервера. Проверь, что backend запущен и доступен по этому же адресу.";
      errorEl.classList.remove("hidden");
    } finally {
      button.disabled = false;
      loadingEl.classList.add("hidden");
    }
  });
}

function renderResults(result) {
  const emptyEl = document.getElementById("results-empty");
  const resultsEl = document.getElementById("results");

  emptyEl.classList.add("hidden");
  resultsEl.classList.remove("hidden");

  renderFit(result);
  renderSkills(result.skills);
  renderList(result.gaps || [], document.getElementById("gaps-list"));
  renderProjects(result.projects || []);
  renderRoadmap(result.roadmap || []);
}

function renderFit(result) {
  const scoreValueEl = document.getElementById("fit-score-value");
  const scoreTextEl = document.getElementById("fit-score-text");

  const score = typeof result.fit_score === "number" ? result.fit_score : 0;
  scoreValueEl.textContent = `${score}%`;

  scoreValueEl.classList.remove("fit-low", "fit-medium", "fit-high");
  if (score < 50) {
    scoreValueEl.classList.add("fit-low");
    scoreTextEl.textContent = "Низкое совпадение — много зон для роста.";
  } else if (score < 80) {
    scoreValueEl.classList.add("fit-medium");
    scoreTextEl.textContent =
      "Среднее совпадение — уже неплохо, но есть, что подтянуть.";
  } else {
    scoreValueEl.classList.add("fit-high");
    scoreTextEl.textContent =
      "Высокое совпадение — ты близок к идеальному кандидату.";
  }

  if (result.fit_explanation) {
    scoreTextEl.textContent = result.fit_explanation;
  }
}

function renderSkills(skills) {
  const mustEl = document.getElementById("skills-must");
  const niceEl = document.getElementById("skills-nice");
  const bonusEl = document.getElementById("skills-bonus");

  fillPills(mustEl, skills?.must_have);
  fillPills(niceEl, skills?.nice_to_have);
  fillPills(bonusEl, skills?.bonus);
}

function fillPills(container, items) {
  container.innerHTML = "";
  if (!Array.isArray(items) || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = "—";
    li.style.opacity = "0.6";
    container.appendChild(li);
    return;
  }

  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    container.appendChild(li);
  }
}

function renderList(items, container) {
  container.innerHTML = "";
  if (!Array.isArray(items) || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = "Нет явных пробелов — сфокусируйся на оттачивании уже имеющихся навыков.";
    li.style.opacity = "0.8";
    container.appendChild(li);
    return;
  }

  for (const gap of items) {
    const li = document.createElement("li");
    li.textContent = gap;
    container.appendChild(li);
  }
}

function renderProjects(projects) {
  const container = document.getElementById("projects-list");
  container.innerHTML = "";

  if (!Array.isArray(projects) || projects.length === 0) {
    const div = document.createElement("div");
    div.className = "card-item";
    div.textContent = "Пока нет конкретных проектов.";
    container.appendChild(div);
    return;
  }

  for (const project of projects) {
    const div = document.createElement("div");
    div.className = "card-item";

    const title = document.createElement("h4");
    title.className = "card-item-title";
    title.textContent = project.title || "Проект без названия";

    const desc = document.createElement("p");
    desc.className = "card-item-text";
    desc.textContent =
      project.description || "Описание проекта не задано моделью.";

    const meta = document.createElement("p");
    meta.className = "card-item-meta";
    if (typeof project.estimated_duration_weeks === "number") {
      meta.textContent = `Оценка: ~${project.estimated_duration_weeks} нед.`;
    } else {
      meta.textContent = "Оценка длительности не задана.";
    }

    div.appendChild(title);
    div.appendChild(desc);
    div.appendChild(meta);
    container.appendChild(div);
  }
}

function renderRoadmap(roadmap) {
  const container = document.getElementById("roadmap-list");
  container.innerHTML = "";

  if (!Array.isArray(roadmap) || roadmap.length === 0) {
    const div = document.createElement("div");
    div.className = "card-item";
    div.textContent = "Roadmap пока пуст — попробуй более детальное описание вакансии и профиля.";
    container.appendChild(div);
    return;
  }

  for (const step of roadmap) {
    const div = document.createElement("div");
    div.className = "card-item";

    const title = document.createElement("h4");
    title.className = "card-item-title";
    title.textContent = `Неделя ${step.week ?? "?"}: ${step.focus || ""}`.trim();

    const tasks = Array.isArray(step.tasks) ? step.tasks : [];
    const meta = document.createElement("p");
    meta.className = "card-item-meta";
    meta.textContent =
      tasks.length > 0
        ? `Задачи: ${tasks.join(", ")}`
        : "Задачи не заданы явно.";

    div.appendChild(title);
    div.appendChild(meta);
    container.appendChild(div);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupForm();
});

