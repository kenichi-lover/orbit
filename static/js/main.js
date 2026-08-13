import { initOrbit } from "./orbit.js";
import { initNav } from "./nav.js";
import { initFilterPanel } from "./filter.js";

window.addEventListener("DOMContentLoaded", () => {
    console.log("Orbit Gallery V0.1");

    initOrbit();
    initNav();
    initFilterPanel();
});

