document.addEventListener('DOMContentLoaded', () => {
    // function to add active class
    const addActiveClass = ele => ele.classList.add("active");

    // function to remove active class
    const removeActiveClass = ele => ele.classList.remove("active");

    // get input sections
    const inputSections = document.querySelectorAll(".auth-section"); // Use the new class name

    // function to check where is active class and remove it
    const checkActiveClass = () => {
        inputSections.forEach(section => {
            if (section.classList.contains("active")) {
                removeActiveClass(section);
            }
        });
    };

    // Add click event listener to each section
    inputSections.forEach(section => {
        const input = section.querySelector('input');
        if (input) {
            // Add active class on focus
            input.addEventListener("focus", () => {
                checkActiveClass(); // Remove from others first
                addActiveClass(section);
            });

            // Optionally remove active class on blur if needed
            input.addEventListener("blur", () => {
                 // Decide if you want to remove active class when focus is lost
                 // removeActiveClass(section);
            });

            // Also activate on clicking the section itself (useful for the icon area)
             section.addEventListener("click", (event) => {
                // Prevent activating if the click is on the input itself (handled by focus)
                if (event.target !== input) {
                    checkActiveClass();
                    addActiveClass(section);
                    input.focus(); // Focus the input when section is clicked
                }
            });
        }
    });

    // Prevent losing active state when clicking within the active section but not on the input
    document.addEventListener('click', (event) => {
        let clickedInsideActiveSection = false;
        inputSections.forEach(section => {
            if (section.classList.contains('active') && section.contains(event.target)) {
                clickedInsideActiveSection = true;
            }
        });

        if (!clickedInsideActiveSection) {
            // If the click is outside any input section, remove active class
            let clickedOnAnyInputSection = false;
             inputSections.forEach(section => {
                 if (section.contains(event.target)) {
                    clickedOnAnyInputSection = true;
                 }
            });
            if (!clickedOnAnyInputSection) {
                 checkActiveClass();
            }
        }
    });

    // Note: The original template JS had logic tied to specific button clicks (like clearing fields).
    // As requested, that logic is NOT included here to avoid interfering with existing functionality.
    // This script only handles the visual "active" state on the input containers.

}); 