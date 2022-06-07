'use strict';

document.addEventListener("DOMContentLoaded", function() {
    addAccordionListeners();
    addCopyDeckstringListeners();
    positionCardTooltips();
})

function positionCardTooltips() {
    // позиционирует tooltip карты в соответствии с ее положением в колоде
    let decks = document.getElementsByClassName("deck");
    for (let i = 0; i < decks.length; i++) {
        let cards = decks[i].getElementsByClassName("deck-card-cell");
        for (let j = 0; j < cards.length; j++) {
            cards[j].firstElementChild.lastElementChild.style.top = -100 - 1000 * j / cards.length + '%';
        }
    }
}

function addAccordionListeners() {
    let accs = document.getElementsByClassName("deck-accordion");
    for (let i = 0; i < accs.length; i++) {
        accs[i].addEventListener("click", showCards);
    }
}

function showCards() {
    this.classList.toggle("deck-accordion-active");
    let cards = this.parentNode.parentNode.parentNode.parentNode.nextElementSibling;
    (cards.style.maxHeight) ?
        cards.style.maxHeight = null :
        cards.style.maxHeight = cards.scrollHeight + "px";
}

function addCopyDeckstringListeners() {
    let copyButtons = document.getElementsByClassName("copy-deck");
    for (let i = 0; i < copyButtons.length; i++) {
        copyButtons[i].addEventListener("click", copyDeckstring);
        copyButtons[i].addEventListener("mouseover", showCopyTooltip);
    }
}

function copyDeckstring() {
    let deckstringInput = this.parentNode.parentNode.nextElementSibling.firstElementChild.firstElementChild;
    if (navigator.clipboard) {    // Если Clipboard API доступно (localhost / HTTPS)
        deckstringInput.select();
        deckstringInput.setSelectionRange(0, 99999);
        navigator.clipboard.writeText(deckstringInput.value);
        let tooltip = this.firstElementChild;
        tooltip.innerHTML = "Copied!";
    } else {
        let controlButtons = this.parentNode.parentNode;
        let copyDeckstringBlock = deckstringInput.parentNode;
        controlButtons.style.display = "none";
        copyDeckstringBlock.style.display = "flex";
        deckstringInput.select();
        deckstringInput.setSelectionRange(0, 99999);
        deckstringInput.nextElementSibling.addEventListener("click", function() {
            controlButtons.style.display = "flex";
            copyDeckstringBlock.style.display = "none";
        });
    }
}

function showCopyTooltip() {
    let tooltip = this.firstElementChild;
    if (navigator.clipboard) {
        tooltip.innerHTML = "Copy deck code";
    } else {
        tooltip.innerHTML = "Show deck code";
    }
}
