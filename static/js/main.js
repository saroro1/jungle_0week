const singleButton = document.getElementById("singleButton");

function openModeModal() {
  document.getElementById("modal_mode").style.display = "block";
}

function closeModeModal() {
  document.getElementById("modal_mode").style.display = "none";
}

function openMultiModal() {

  closeModeModal();
  
  document.getElementById("modal_multi").style.display = "block";
}

function closeMultiModal() {
  document.getElementById("modal_multi").style.display = "none";
}

function openMakeRoomModal() {

  closeMultiModal();
  
  document.getElementById("modal_MakeRoom").style.display = "block";
}

function closeMakeRoomModal() {
  document.getElementById("modal_MakeRoom").style.display = "none";
}

function openJoinRoomModal() {

  closeMultiModal();
  
  document.getElementById("modal_JoinRoom").style.display = "block";
}

function closeJoinRoomModal() {
  document.getElementById("modal_JoinRoom").style.display = "none";
}

function goToMulti(isHost) {
  const typeDropdwon = document.getElementById("modeSelectDropdown");
  window.location.href = `/game/multi/${typeDropdwon.value}/${isHost?"host":"guest"}`;
}


function updateStartAndRankingButtons() {
  const selectBox = document.getElementById("modeSelectDropdown");
  const rankingButton = document.getElementById("rankingButton");
  const selectedMode = selectBox.value;

  const rankingUrlTemplate =
    "{{ url_for('game.ranking', type_word='TEMP_WORD', page=0) }}";

  if (selectedMode) {
    rankingButton.href = rankingUrlTemplate.replace(
      "TEMP_WORD",
      encodeURIComponent(selectedMode)
    );
  } else {
    rankingButton.href = rankingUrlTemplate.replace("TEMP_WORD", "");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // 이벤트 연결
  document.getElementById("startButton").addEventListener("click", openModeModal);
  document.getElementById("closeButton").addEventListener("click", closeModeModal);
  // document.getElementById("battlemodeButton").addEventListener("click", openMultiModal);

  // 멀티모드 닫기 버튼은 ID가 중복되지 않게 따로 줘야 함!
  const closeMultiBtn = document.querySelector("#modal_multi .close-btn");
  if (closeMultiBtn) {
    closeMultiBtn.addEventListener("click", closeMultiModal);
  }

  document
    .getElementById("modeSelectDropdown")
    .addEventListener("change", updateStartAndRankingButtons);

  updateStartAndRankingButtons();
});

singleButton.addEventListener('click',()=>{
  console.log("click");
  const typeDropdwon = document.getElementById("modeSelectDropdown");
  window.location.href = `/game/play/${typeDropdwon.value}`;
});