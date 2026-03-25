$(function() {
  // Disable search until input contains values
  const source = document.getElementById('autoComplete');
  const inputHandler = function(e) {
    if(e.target.value==""){
      $('.movie-button').attr('disabled', true);
    }
    else{
      $('.movie-button').attr('disabled', false);
    }
  }
  source.addEventListener('input', inputHandler);

  $('.movie-button').on('click',function(){
    var title = $('.movie').val();
    
    $('.trending-container').hide();
    $('.genres-container').hide();
    $('#home-genre-section').hide();
    $('#home-btn').fadeIn(300).css('display', 'flex'); 
    
    if (title=="") {
      $('.results').css('display','none');
      $('.fail').css('display','block');
    }
    else{
      load_details(title);
    }
  });
});

// Triggered when any movie card is clicked
function recommendcard(e){
  var title = e.getAttribute('title');
  var explicit_id = e.getAttribute('data-id');
  
  $('.fail').hide();
  $('#loader').fadeIn();
  
  load_details(title, explicit_id);
}

// Step 1: Get similarity recommendations from our backend
function load_details(title, explicit_id=null){
  var my_api_key = '5ce2ef2d7c461dea5b4e04900d1c561e';

  // First, resolve TMDB ID
  if (explicit_id && explicit_id !== "null" && explicit_id !== "undefined") {
    // We already have the ID — go straight to similarity + details
    movie_recs(title, explicit_id, my_api_key);
  } else {
    // Search TMDB for the movie to get its ID
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

          // Pick result with most votes to avoid obscure title collisions
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

// Step 2: POST to our Flask /similarity, then send everything to /get_details
function movie_recs(movie_title, movie_id, my_api_key){
  $.ajax({
    type: 'POST',
    url: "/similarity",
    data: {'name': movie_title, 'movie_id': movie_id},
    success: function(recs){
      var not_in_db = false;
      var movie_arr = [];

      if(recs === "__NOT_IN_DB__"){
        not_in_db = true;
      } else {
        movie_arr = recs.split('---').filter(Boolean);
      }

      // Step 3: Send movie_id + rec titles to backend — backend does ALL TMDB fetching in parallel
      var payload = {
          movie_id: movie_id,
          rec_titles: movie_arr,
          not_in_db: not_in_db
      };
      console.log('[CineMatch] /get_details payload:', payload);
      $.ajax({
        type: 'POST',
        url: "/get_details",
        contentType: 'application/json',
        data: JSON.stringify(payload),
        dataType: 'html',
        complete: function(){
          $("#loader").delay(300).fadeOut();
        },
        success: function(response){
          $('.trending-container').hide();
          $('.genres-container').hide();
          $('#home-genre-section').hide();
          $('#home-btn').fadeIn(300).css('display', 'flex');
          $('.results').html(response).show();
          $('#autoComplete').val('');
          $(window).scrollTop(0);
        },
        error: function(){
          alert("Error loading movie details.");
          $("#loader").delay(500).fadeOut();
        }
      });
    },
    error: function(){
      alert("Error getting recommendations.");
      $("#loader").delay(500).fadeOut();
    },
  });
}
