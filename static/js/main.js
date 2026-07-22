import { initOrbit } from "./orbit.js";
import { initNav } from "./nav.js";

window.addEventListener("DOMContentLoaded", () => {
    console.log("Orbit Gallery V0.1");

    initOrbit();
    initNav();
});

