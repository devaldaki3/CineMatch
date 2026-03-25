$(function() {
  const source = document.getElementById('autoComplete');
  const inputHandler = function(e) {
    if(e.target.value==""){
      $('.movie-button').attr('disabled', true);
    } else {
      $('.movie-button').attr('disabled', false);
    }
  }
  source.addEventListener('input', inputHandler);

  $('.movie-button').on('click',function(){
    var title = $('.movie').val();
    $('#loader').fadeIn();
    
    if (title=="") {
      $('.results').css('display','none');
      $('.fail').css('display','block');
    } else {
      load_details(title);
    }
  });
});

function recommendcard(e){
  var title = e.getAttribute('title');
  var explicit_id = e.getAttribute('data-id');
  $('.fail').hide();
  $('#loader').fadeIn();
  load_details(title, explicit_id);
}

function load_details(title, explicit_id=null){
  var my_api_key = '5ce2ef2d7c461dea5b4e04900d1c561e';

  if (explicit_id && explicit_id !== "null" && explicit_id !== "undefined") {
    movie_recs(title, explicit_id, my_api_key);
  } else {
    $.ajax({
      type: 'GET',
      url: 'https://api.themoviedb.org/3/search/movie?api_key=' + my_api_key + '&query=' + encodeURIComponent(title),
      success: function(movie){
        if(movie.results.length < 1){
          $('.fail').css('display','block');
          $('.results').css('display','none');
          $("#loader").delay(500).fadeOut();
        } else {
          $("#loader").fadeIn();
          $('.fail').css('display','none');
          var best_movie = movie.results[0];
          var max_votes = -1;
          for (var i = 0; i < movie.results.length; i++) {
            if (movie.results[i].vote_count > max_votes) {
              max_votes = movie.results[i].vote_count;
              best_movie = movie.results[i];
            }
          }
          movie_recs(title, best_movie.id, my_api_key);
        }
      },
      error: function(){
        alert('Invalid Request');
        $("#loader").delay(500).fadeOut();
      },
    });
  }
}

function movie_recs(movie_title, movie_id, my_api_key){

  var similarity_promise = $.ajax({
    type: 'POST',
    url: "/similarity",
    data: {'name': movie_title, 'movie_id': movie_id}
  });

  var details_promise = $.ajax({
    type: 'POST',
    url: "/get_details",
    contentType: 'application/json',
    data: JSON.stringify({ movie_id: movie_id, rec_titles: [], not_in_db: false }),
    dataType: 'html'
  });

  details_promise.done(function(response){
    $("#loader").fadeOut();
    $('.trending-container').hide();
    $('.genres-container').hide();
    $('#home-genre-section').hide();
    $('#direct-home-btn').fadeIn(300).css('display', 'flex');
    $('.results').html(response).show();
    $('#autoComplete').val('');
    $(window).scrollTop(0);

    similarity_promise.done(function(recs){
      if(recs === "__NOT_IN_DB__" || !recs){
        $('#rec-loader-section').hide();
        $('#rec-inject-section').html(
          '<div class="movie" style="color:#E8E8E8;text-align:center;margin:30px auto;max-width:600px;">' +
          '<div style="background:rgba(229,9,20,0.08);border:1px solid rgba(229,9,20,0.3);border-radius:16px;padding:28px 32px;">' +
          '<i class="fa fa-database" style="font-size:2.5rem;color:#e50914;margin-bottom:14px;display:block;"></i>' +
          '<h4 style="color:white;font-weight:700;margin-bottom:10px;">Not in Our Database</h4>' +
          '<p style="color:#aaa;font-size:0.97rem;margin:0;">This movie is not part of our database, so we can\'t suggest similar movies.</p>' +
          '</div></div>'
        ).show();
        return;
      }

      var movie_arr = recs.split('---').filter(Boolean);
      if(movie_arr.length === 0){
        $('#rec-loader-section').hide();
        return;
      }

      $.ajax({
        type: 'POST',
        url: '/get_rec_posters',
        contentType: 'application/json',
        data: JSON.stringify({rec_titles: movie_arr}),
        success: function(data){
          var result = JSON.parse(data);
          var movies = result.movies;
          var posters = result.posters;
          var ids = result.ids;

          var html = '<div class="movie" style="color: #E8E8E8;">';
          html += '<center><h3>RECOMMENDED MOVIES FOR YOU</h3>';
          html += '<h5>(Click any of the movies to get recommendation)</h5></center></div>';
          html += '<div class="movie-content">';
          for(var i = 0; i < movies.length; i++){
            html += '<div class="card" style="width: 15rem;" title="' + movies[i] + '" data-id="' + ids[i] + '" onclick="recommendcard(this)">';
            html += '<div class="imghvr">';
            html += '<img class="card-img-top" height="360" width="240" alt="' + movies[i] + ' - poster" src="' + posters[i] + '">';
            html += '<figcaption class="fig"><button class="card-btn btn btn-danger">Click Me</button></figcaption>';
            html += '</div>';
            html += '<div class="card-body"><h5 class="card-title">' + movies[i] + '</h5></div>';
            html += '</div>';
          }
          html += '</div>';

          $('#rec-loader-section').hide();
          $('#rec-inject-section').html(html).show();
        },
        error: function(){
          $('#rec-loader-section').hide();
        }
      });
    });

    similarity_promise.fail(function(){
      $('#rec-loader-section').hide();
    });
  });

  details_promise.fail(function(){
    alert("Error loading movie details.");
    $("#loader").fadeOut();
  });
}
