'use strict';

$(document).ready(function(){

    // Удаляет пустые поля из GET-запроса

    $("#searchForm").submit(function() {
		$(this).find(":input").filter(function(){ return !this.value; }).attr("disabled", "disabled");
		return true;    // сабмит формы
	});

	// Разблокировка полей при загрузке страницы в случае, если юзер после сабмита вернулся на страницу
	$("#searchForm").find(":input").prop("disabled", false);
});
