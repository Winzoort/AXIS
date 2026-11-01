// WEATHERMT - FUNCIONES PRINCIPALES

// MENÚ PARA CELULARES
const menuToggle = document.getElementById("menuToggle");
const navMenu = document.getElementById("navMenu");

menuToggle.addEventListener("click", () => {
    navMenu.classList.toggle("active");
});

// CERRAR EL MENÚ AL SELECCIONAR UNA OPCIÓN
const navLinks = navMenu.querySelectorAll("a");

navLinks.forEach(link => {
    link.addEventListener("click", () => {
        navMenu.classList.remove("active");
    });
});

// AÑO AUTOMÁTICO EN EL PIE DE PÁGINA
const year = document.getElementById("year");

year.textContent = new Date().getFullYear();

// =========================
// VENTANA MODAL DE CONTACTO
// =========================

// Obtener elementos
const contactButton = document.getElementById("discordButton");
const contactModal = document.getElementById("contactModal");
const closeModal = document.getElementById("closeModal");

// ABRIR LA VENTANA
contactButton.addEventListener("click", () => {
    contactModal.classList.add("active");
});

// CERRAR CON EL BOTÓN X
closeModal.addEventListener("click", () => {
    contactModal.classList.remove("active");
});

// CERRAR AL PRESIONAR FUERA DE LA VENTANA
contactModal.addEventListener("click", (event) => {
    if (event.target === contactModal) {
        contactModal.classList.remove("active");
    }
});

// CERRAR AL PRESIONAR ESCAPE
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        contactModal.classList.remove("active");
    }
});
// =====================================
// VENTANA EMERGENTE DEL CORREO AXIS
// =====================================

// Obtener los elementos HTML
const emailButton = document.getElementById("emailButton");
const emailModal = document.getElementById("emailModal");
const closeEmailModal = document.getElementById("closeEmailModal");
const copyEmail = document.getElementById("copyEmail");
const emailText = document.getElementById("emailText");
const copyMessage = document.getElementById("copyMessage");


// ABRIR LA VENTANA
emailButton.addEventListener("click", () => {
    emailModal.classList.add("active");
});


// CERRAR LA VENTANA
closeEmailModal.addEventListener("click", () => {
    emailModal.classList.remove("active");
});


// CERRAR AL PRESIONAR FUERA DE LA VENTANA
emailModal.addEventListener("click", (event) => {
    if (event.target === emailModal) {
        emailModal.classList.remove("active");
    }
});


// CERRAR CON LA TECLA ESCAPE
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        emailModal.classList.remove("active");
    }
});


// COPIAR EL CORREO
copyEmail.addEventListener("click", async () => {
    const email = emailText.textContent.trim();

    try {
        await navigator.clipboard.writeText(email);

        copyMessage.textContent = "Email copied successfully!";
        copyEmail.textContent = "Copied!";

    } catch (error) {
        copyMessage.textContent = "Could not copy. Please copy it manually.";
    }
});