'use strict';

$(document).ready(function() {
    $('#getRandomDeckstring').click(function() {
        $.ajax({
            data: {deckstring: 'random'},
            url: "random_deckstring/",
            success: function(response) {
                $('#form-deckstring').val(response.deckstring);
            },
            error: function(response) {
                console.log(response.responseJSON.errors);
            }
        });
    });
});
