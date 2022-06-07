'use strict';

$(document).ready(function(){

    let r = document.querySelector(':root');
    let rs = getComputedStyle(r);
    let cards = $(".multiclass");

    for (let i = 0; i < cards.length; i++) {
        let cssVars = getCssVars(cards[i]);

        /*
        обрабатываются случаи 2-х и 3-х классовых карт -
        других типов мультиклассовых карт в Hearthstone нет
        и, скорее всего, не будет
        */
        switch(cssVars.length) {
            case 2: {
                let cardStyle = `linear-gradient(90deg,
                                                 ${rs.getPropertyValue(cssVars[0].first)},
                                                 ${rs.getPropertyValue(cssVars[1].first)})`;
                let hoverStyle = `linear-gradient(90deg,
                                                  ${rs.getPropertyValue(cssVars[0].first)},
                                                  ${rs.getPropertyValue(cssVars[0].second)},
                                                  ${rs.getPropertyValue(cssVars[1].first)})`;
                cards[i].style.backgroundImage = cardStyle;
                cards[i].addEventListener("mouseenter", function(){
                    cards[i].style.backgroundImage = hoverStyle;
                });
                cards[i].addEventListener("mouseleave", function(){
                    cards[i].style.backgroundImage = cardStyle;
                });
            }; break;
            case 3: {
                let cardStyle = `linear-gradient(90deg,
                                                 ${rs.getPropertyValue(cssVars[0].first)},
                                                 ${rs.getPropertyValue(cssVars[1].first)},
                                                 ${rs.getPropertyValue(cssVars[2].first)})`;
                let hoverStyle = `linear-gradient(90deg,
                                                  ${rs.getPropertyValue(cssVars[0].first)},
                                                  ${rs.getPropertyValue(cssVars[0].second)},
                                                  ${rs.getPropertyValue(cssVars[1].first)},
                                                  ${rs.getPropertyValue(cssVars[2].second)},
                                                  ${rs.getPropertyValue(cssVars[2].first)})`
                cards[i].style.backgroundImage = cardStyle;
                cards[i].addEventListener("mouseenter", function(){
                    cards[i].style.backgroundImage = hoverStyle;
                });
                cards[i].addEventListener("mouseleave", function(){
                    cards[i].style.backgroundImage = cardStyle;
                });
            }; break;
            default: break;
        }
    }
});

function getCssVars(card) {
    /*
    Возвращает объект с :root-переменными CSS для цвета соответствующих классов
    */
    for (let cls of card.classList) {
        if (cls.includes('-')) {
            let classes = cls.split('-');
            for (let i = 0; i < classes.length; i++) {
                classes[i] = {first: `--${classes[i]}-1`, second: `--${classes[i]}-2`};
            }
            return classes;
        }
    }
}
