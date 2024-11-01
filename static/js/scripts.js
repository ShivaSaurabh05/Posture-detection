let goodPostureTime = 0;
let badPostureTime = 0;
let currentPosture = "Good Posture";

function updatePostureTime() {
  fetch("/posture_status")
    .then((response) => response.json())
    .then((data) => {
      currentPosture = data.posture;
      document.getElementById(
        "posture-status"
      ).innerText = `Posture: ${currentPosture}`;
    });
}

// Update timers every second
setInterval(() => {
  // Check the current posture
  updatePostureTime();

  // Increment the appropriate posture timer
  if (currentPosture === "Good Posture") {
    goodPostureTime = goodPostureTime + 1;
    document.getElementById(
      "good-posture-timer"
    ).innerText = `Good Posture Time: ${goodPostureTime}s`;
  } else {
    badPostureTime = badPostureTime + 1;
    document.getElementById(
      "bad-posture-timer"
    ).innerText = `Bad Posture Time: ${badPostureTime}s`;
  }
}, 1000);
