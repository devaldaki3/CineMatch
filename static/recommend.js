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
    var my_api_key = '5ce2ef2d7c461dea5b4e04900d1c561e';
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
      load_details(my_api_key,title);
    }
  });
});

// Triggered when any movie card is clicked
function recommendcard(e){
  var my_api_key = '5ce2ef2d7c461dea5b4e04900d1c561e';
  var title = e.getAttribute('title');
  var explicit_id = e.getAttribute('data-id');
  
  // Show loader; hide/transition happens only after new content is ready
  $('.fail').hide();
  $('#loader').fadeIn();
  
  load_details(my_api_key, title, explicit_id);
}

// Fetch movie info from TMDB. Uses explicit ID if available (card click), else searches by title (search bar).
function load_details(my_api_key, title, explicit_id=null){
  if (explicit_id && explicit_id !== "null" && explicit_id !== "undefined") {
    $.ajax({
      type: 'GET',
      url: 'https://api.themoviedb.org/3/movie/' + explicit_id + '?api_key=' + my_api_key,
      success: function(movie){
        $("#loader").fadeIn();
        $('.fail').css('display','none');
        $('.results').delay(1000).css('display','block');
        var movie_id = movie.id;
        var movie_title = movie.title || movie.original_title;
        movie_recs(movie_title, movie_id, my_api_key, title);
      },
      error: function(){
        alert('Invalid Request');
        $("#loader").delay(500).fadeOut();
      },
    });
  } else {
    // Fallback: text search (no ID available)
    $.ajax({
      type: 'GET',
      url:'https://api.themoviedb.org/3/search/movie?api_key='+my_api_key+'&query='+title,
      success: function(movie){
        if(movie.results.length<1){
          $('.fail').css('display','block');
          $('.results').css('display','none');
          $("#loader").delay(500).fadeOut();
        }
        else{
          $("#loader").fadeIn();
          $('.fail').css('display','none');
          $('.results').delay(1000).css('display','block');
          
          // Pick the result with the most votes to avoid obscure title collisions
          var best_movie = movie.results[0];
          var max_votes = -1;
          for (var i = 0; i < movie.results.length; i++) {
            if (movie.results[i].vote_count > max_votes) {
              max_votes = movie.results[i].vote_count;
              best_movie = movie.results[i];
            }
          }
          
          var movie_id = best_movie.id;
          var movie_title = best_movie.title;
          movie_recs(movie_title, movie_id, my_api_key, title);
        }
      },
      error: function(){
        alert('Invalid Request');
        $("#loader").delay(500).fadeOut();
      },
    });
  }
}

// POST to Flask /similarity to get recommended movie titles
function movie_recs(movie_title, movie_id, my_api_key, original_title){
  $.ajax({
    type:'POST',
    url:"/similarity",
    data:{'name':movie_title, 'movie_id': movie_id},
    success: function(recs){
      if(recs=="__NOT_IN_DB__"){
        // TMDB title didn't match our dataset — retry with user's original typed title
        if(original_title && original_title.toLowerCase() !== movie_title.toLowerCase()){
          $.ajax({
            type:'POST',
            url:"/similarity",
            data:{'name': original_title},
            success: function(recs2){
              if(recs2=="__NOT_IN_DB__"){
                get_movie_details(movie_id, my_api_key, [], movie_title, true);
              } else {
                var movie_arr = recs2.split('---');
                var arr = [];
                for(const movie in movie_arr){ arr.push(movie_arr[movie]); }
                get_movie_details(movie_id, my_api_key, arr, movie_title, false);
              }
            },
            error: function(){
              get_movie_details(movie_id, my_api_key, [], movie_title, true);
            }
          });
        } else {
          get_movie_details(movie_id, my_api_key, [], movie_title, true);
        }
      }
      else {
        $('.fail').css('display','none');
        $('.results').css('display','block');
        var movie_arr = recs.split('---');
        var arr = [];
        for(const movie in movie_arr){
          arr.push(movie_arr[movie]);
        }
        get_movie_details(movie_id,my_api_key,arr,movie_title, false);
      }
    },
    error: function(){
      alert("error recs");
      $("#loader").delay(500).fadeOut();
    },
  }); 
}

// Fetch full movie specifics via TMDB ID
function get_movie_details(movie_id,my_api_key,arr,movie_title,not_in_db) {
  $.ajax({
    type:'GET',
    url:'https://api.themoviedb.org/3/movie/'+movie_id+'?api_key='+my_api_key,
    success: function(movie_details){
      show_details(movie_details,arr,movie_title,my_api_key,movie_id,not_in_db);
    },
    error: function(){
      alert("API Error!");
      $("#loader").delay(500).fadeOut();
    },
  });
}

// Gather & dispatch payload to Flask for templating and sentiment analysis
function show_details(movie_details,arr,movie_title,my_api_key,movie_id,not_in_db){
  var imdb_id = movie_details.imdb_id;
  var poster = 'https://image.tmdb.org/t/p/original'+movie_details.poster_path;
  var overview = movie_details.overview;
  var genres = movie_details.genres;
  var rating = movie_details.vote_average;
  var vote_count = movie_details.vote_count;
  var release_date = new Date(movie_details.release_date);
  var runtime = parseInt(movie_details.runtime);
  var status = movie_details.status;
  var genre_list = []
  for (var genre in genres){
    genre_list.push(genres[genre].name);
  }
  var my_genre = genre_list.join(", ");
  if(runtime%60==0){
    runtime = Math.floor(runtime/60)+" hour(s)"
  }
  else {
    runtime = Math.floor(runtime/60)+" hour(s) "+(runtime%60)+" min(s)"
  }
  var poster_data = get_movie_posters(arr,my_api_key);
  var arr_poster = poster_data.posters;
  var arr_ids = poster_data.ids;
  
  movie_cast = get_movie_cast(movie_id,my_api_key);
  
  ind_cast = get_individual_cast(movie_cast,my_api_key);
  
  details = {
    'title':movie_title,
      'cast_ids':JSON.stringify(movie_cast.cast_ids),
      'cast_names':JSON.stringify(movie_cast.cast_names),
      'cast_chars':JSON.stringify(movie_cast.cast_chars),
      'cast_profiles':JSON.stringify(movie_cast.cast_profiles),
      'cast_bdays':JSON.stringify(ind_cast.cast_bdays),
      'cast_bios':JSON.stringify(ind_cast.cast_bios),
      'cast_places':JSON.stringify(ind_cast.cast_places),
      'imdb_id':imdb_id,
      'poster':poster,
      'genres':my_genre,
      'overview':overview,
      'rating':rating,
      'vote_count':vote_count.toLocaleString(),
      'release_date':release_date.toDateString().split(' ').slice(1).join(' '),
      'runtime':runtime,
      'status':status,
      'rec_movies':JSON.stringify(arr),
      'rec_posters':JSON.stringify(arr_poster),
      'rec_ids':JSON.stringify(arr_ids),
      'not_in_db': not_in_db ? '1' : '0',
  }

  $.ajax({
    type:'POST',
    data:details,
    url:"/recommend",
    dataType: 'html',
    complete: function(){
      $("#loader").delay(500).fadeOut();
    },
    success: function(response) {
      // Hide home sections and render the movie details page
      $('.trending-container').hide();
      $('.genres-container').hide();
      $('#home-genre-section').hide();
      $('#home-btn').fadeIn(300).css('display', 'flex');
      $('.results').html(response).show();
      $('#autoComplete').val('');
      $(window).scrollTop(0);
    }
  });
}

// Fetch enriched metadata for individual actors
function get_individual_cast(movie_cast,my_api_key) {
    cast_bdays = [];
    cast_bios = [];
    cast_places = [];
    for(var cast_id in movie_cast.cast_ids){
      $.ajax({
        type:'GET',
        url:'https://api.themoviedb.org/3/person/'+movie_cast.cast_ids[cast_id]+'?api_key='+my_api_key,
        async:false,
        success: function(cast_details){
          var bday = cast_details.birthday ? (new Date(cast_details.birthday)).toDateString().split(' ').slice(1).join(' ') : "Not Available";
          var bio = cast_details.biography || "No biography available.";
          var place = cast_details.place_of_birth || "Not Available";
          cast_bdays.push(bday);
          cast_bios.push(bio);
          cast_places.push(place);
        }
      });
    }
    return {cast_bdays:cast_bdays,cast_bios:cast_bios,cast_places:cast_places};
  }

// Fetch top billed cast IDs and profiles
function get_movie_cast(movie_id,my_api_key){
    cast_ids= [];
    cast_names = [];
    cast_chars = [];
    cast_profiles = [];

    top_10 = [0,1,2,3,4,5,6,7,8,9];
    $.ajax({
      type:'GET',
      url:"https://api.themoviedb.org/3/movie/"+movie_id+"/credits?api_key="+my_api_key,
      async:false,
      success: function(my_movie){
        if (!my_movie || !my_movie.cast) {
            return; // Guard: TMDB returned no cast
        }
        var limit = Math.min(10, my_movie.cast.length);
        for(var i = 0; i < limit; i++){
          cast_ids.push(my_movie.cast[i].id);
          cast_names.push(my_movie.cast[i].name);
          cast_chars.push(my_movie.cast[i].character);
          
          if(my_movie.cast[i].profile_path) {
            cast_profiles.push("https://image.tmdb.org/t/p/original" + my_movie.cast[i].profile_path);
          } else {
            // Fallback avatar using actor initials
            cast_profiles.push("https://ui-avatars.com/api/?name=" + encodeURIComponent(my_movie.cast[i].name) + "&size=240&background=111&color=fff");
          }
        }
      },
      error: function(){
        alert("Invalid Request!");
        $("#loader").delay(500).fadeOut();
      }
    });

    return {cast_ids:cast_ids,cast_names:cast_names,cast_chars:cast_chars,cast_profiles:cast_profiles};
  }

// Fetch posters and IDs for recommended movies
function get_movie_posters(arr,my_api_key){
  var arr_poster_list = [];
  var arr_id_list = [];
  for(var m in arr) {
    $.ajax({
      type:'GET',
      url:'https://api.themoviedb.org/3/search/movie?api_key='+my_api_key+'&query='+arr[m],
      async: false,
      success: function(m_data){
        if (!m_data.results || m_data.results.length === 0) {
          arr_poster_list.push('');
          arr_id_list.push('');
          return;
        }
        // Grab the most popular match by vote_count to avoid indie short-film name collisions
        var best_match = m_data.results[0];
        var max_v = -1;
        for (var i = 0; i < m_data.results.length; i++) {
          if (m_data.results[i].vote_count > max_v) {
            max_v = m_data.results[i].vote_count;
            best_match = m_data.results[i];
          }
        }
        arr_poster_list.push('https://image.tmdb.org/t/p/original'+best_match.poster_path);
        arr_id_list.push(best_match.id);
      },
      error: function(){
        arr_poster_list.push('');
        arr_id_list.push('');
      },
    });
  }
  return {posters: arr_poster_list, ids: arr_id_list};
}
