document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll('.predict-row');

    // Add blink animation style
    addBlinkAnimationStyle();

    // Initialize row validation
    rows.forEach(initializeRowValidation);

    // Add form submission event listener
    document.querySelector('form').addEventListener('submit', validateFormOnSubmit);

    // Fade out played rows
    fadeOutPlayedRows();

    function addBlinkAnimationStyle() {
        const style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = `
        @keyframes blink {
          0% { border-color: #dc3545; }
          50% { border-color: transparent; }
          100% { border-color: #dc3545; }
        }
        .blink {
          animation: blink 1s infinite;
        }
      `;
        document.getElementsByTagName('head')[0].appendChild(style);
    }

    function initializeRowValidation(row) {
        const homeScore = row.querySelector('input[name="home_score"]');
        const awayScore = row.querySelector('input[name="away_score"]');

        function validateRow() {
            if (homeScore.value !== "" && awayScore.value === "") {
                setBlinkEffect(awayScore, true);
                setBlinkEffect(homeScore, false);
            } else if (homeScore.value === "" && awayScore.value !== "") {
                setBlinkEffect(homeScore, true);
                setBlinkEffect(awayScore, false);
            } else {
                setBlinkEffect(homeScore, false);
                setBlinkEffect(awayScore, false);
            }
        }

        homeScore.addEventListener('input', validateRow);
        awayScore.addEventListener('input', validateRow);
    }

    function setBlinkEffect(element, shouldBlink) {
        if (shouldBlink) {
            element.classList.add('blink');
        } else {
            element.classList.remove('blink');
        }
    }

    function validateFormOnSubmit(event) {
        let formIsValid = true;

        rows.forEach(row => {
            const homeScore = row.querySelector('input[name="home_score"]');
            const awayScore = row.querySelector('input[name="away_score"]');

            if ((homeScore.value !== "" && awayScore.value === "") || (homeScore.value === "" && awayScore.value !== "")) {
                formIsValid = false;
                setBlinkEffect(homeScore, true);
                setBlinkEffect(awayScore, true);
                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });

        if (!formIsValid) {
            event.preventDefault();
        }
    }

    function fadeOutPlayedRows() {
        document.querySelectorAll('.played').forEach(input => {
            input.parentElement.style.opacity = "0.4";
        });
    }
});
