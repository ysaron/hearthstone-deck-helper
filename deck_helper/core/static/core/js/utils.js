function showDeckSaveForm() {
  var form = document.getElementById("deckSaveForm");
  var ctrl_buttons = document.getElementById("deckControlButtons2");
  form.style.display = "flex";
  ctrl_buttons.style.display = "none";
}

function showDeckRenameForm() {
  var form = document.getElementById("deckRenameForm");
  var ctrl_buttons = document.getElementById("deckControlButtons");
  form.style.display = "flex";
  ctrl_buttons.style.display = "none";
}

function showDeckDeleteForm() {
  var form = document.getElementById("deckDeleteForm");
  var ctrl_buttons = document.getElementById("deckControlButtons");
  form.style.display = "flex";
  ctrl_buttons.style.display = "none";
}

function hideDeckSaveForm() {
  var form = document.getElementById("deckSaveForm");
  var ctrl_buttons = document.getElementById("deckControlButtons2");
  form.style.display = "none";
  ctrl_buttons.style.display = "flex";
}

function hideDeckDeleteForm() {
  var form = document.getElementById("deckDeleteForm");
  var ctrl_buttons = document.getElementById("deckControlButtons");
  form.style.display = "none";
  ctrl_buttons.style.display = "flex";
}

function hideDeckRenameForm() {
  var form = document.getElementById("deckRenameForm");
  var ctrl_buttons = document.getElementById("deckControlButtons");
  form.style.display = "none";
  ctrl_buttons.style.display = "flex";
}

function copyToClipboard() {
  let copyDeckBlock = document.getElementById("deckstringToCopy");
  let copyText = copyDeckBlock.firstElementChild;
  if (navigator.clipboard) {    // Если Clipboard API доступно (localhost / HTTPS)
      copyText.select();
      copyText.setSelectionRange(0, 99999);     // Для мобильных устройств
      navigator.clipboard.writeText(copyText.value);
      let tooltip = document.getElementById("copyTooltip");
      tooltip.innerHTML = "Copied!";
  } else {
      let ctrl_buttons = document.getElementById("deckControlButtons");
      if (ctrl_buttons == undefined) ctrl_buttons = document.getElementById("deckControlButtons2");
      ctrl_buttons.style.display = "none";
      copyDeckBlock.style.display = "flex";
      copyText.select();
      copyText.setSelectionRange(0, 99999);
      copyText.nextElementSibling.addEventListener("click", function() {
          ctrl_buttons.style.display = "flex";
          copyDeckBlock.style.display = "none";
      });
  }
}

function tooltipFunc() {
  var tooltip = document.getElementById("copyTooltip");
  if (navigator.clipboard) {
        tooltip.innerHTML = "Copy deck code";
    } else {
        tooltip.innerHTML = "Show deck code";
    }
}

function clearDeckstringField() {
    $('#form-deckstring').val('').focus();
}

function mail() {
    let btn = $('#contactBtn');
    let endpoint = btn.attr("data-url");
    $.ajax({
        data: {email: true},
        url: endpoint,
        success: function(response) {btn.empty().text(response.email);},
        error: function(response) {console.log(response.responseJSON.errors);}
    });
}

function showRenderForm() {
    let btn = document.getElementById('deckRenderDiv');
    let renderForm = document.getElementById('renderForm');
    btn.style.display = "none";
    renderForm.style.display = "flex";
}

function render() {

    document.getElementById('renderForm').style.display = "none";
    let loading = document.getElementById('deckRenderLoading');
    loading.style.display = "block";
    document.getElementById('renderForm').style.display = "none";

    let btn = $('#renderForm');
    let deckId = btn.attr('datasrc');
    let name = $('#renderName').val();
    let lang = $('input[name=renderLang]:checked', btn.find('form')).val();
    $.ajax({
        data: {
            render: true,
            deck_id: deckId,
            name: name,
            language: lang
        },
        url: 'get_render/',
        success: function(response) {
            let a = document.createElement("a");
            a.setAttribute("href", response.render);
            a.setAttribute("target", "_blank");
            a.setAttribute("display", "block");
            a.setAttribute("width", "100%");
            a.setAttribute("height", "100%");

            let deckRender = document.createElement("img");
            deckRender.src = response.render;

            let div = document.getElementById("deckRenderPlaceholder");

            let width = "";
            let height = "";
            if (response.width >= response.height) {
                width = "308px";
                height = "auto";
            }
            else {
                width = "auto";
                height = "308px";
            }
            deckRender.setAttribute("width", width);
            deckRender.setAttribute("height", height);
            deckRender.setAttribute("alt", "Deck Render");

            a.appendChild(deckRender);

            loading.style.display = "none";
            div.style.display = "flex";
            div.appendChild(a);
        },
        error: function(response) {console.log(response.responseJSON.errors);}
    });
}

// Открытие Dropdown по клику на Decks
function decksDropdown() {
    document.getElementById("decksDropdown").style.display = "block";
}

// Закрытие Dropdown
window.onclick = function(e) {
    if (!e.target.matches('.dropbtn')) {
        document.getElementById("decksDropdown").style.display = "none";
    }
}
