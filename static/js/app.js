        angular.module('myApp', ['ngCookies'])
            .controller('HomeCtrl', function($scope, $http, $timeout, $window, $cookies) {

				$scope.info = {};

				$scope.showAdd = true;
                $scope.loadComplete = false;
                $scope.refreshing = false;

                $scope.lastRefresh = "";

                //Sorting
                $scope.orderByField = 'device';
                $scope.reverseSort = false;

                $scope.tickerName = "";

                function getCurrentDate() {
                var d = new Date(),
                    minutes = d.getMinutes().toString().length == 1 ? '0'+d.getMinutes() : d.getMinutes(),
                    hours = d.getHours() > 12 ? d.getHours() - 12 : d.getHours(),
                    ampm = d.getHours() >= 12 ? 'pm' : 'am',
                    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
                    days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
                return d.getMonth()+'/'+d.getDate()+'/'+d.getFullYear()+' - '+hours+':'+minutes+ampm;
                }

                //Cookies keep time in minutes to check for 3 minute intervals.
                var getLastUpdateCookie = $cookies.get("lastUpdate");
                if ( getLastUpdateCookie )
                  $scope.lastRefresh = getLastUpdateCookie;

                var now = new $window.Date(),
                    // this will set cookie expiration to 6 months
                    exp = new $window.Date(now.getFullYear(), now.getMonth()+6, now.getDate());
                $scope.pollData = function (interval) {
                    interval = interval || 5000;

                    (function p() {
                        var startTime = (new Date()).getMinutes();
                        var getStartTimeCookie = $cookies.get("startTime");

                        //Doesn't exist? Let's set it. Let's also refresh here.
                        if ( !getStartTimeCookie ) {
                            $cookies.put("startTime", (new Date).getMinutes(), {expires: exp});
                            $cookies.put("lastUpdate", getCurrentDate(), {expires: exp});

                            $scope.lastRefresh = getCurrentDate();
                            refreshTickers();
                        }

                        console.log("Time: "+(new Date).getMinutes()+"\tStart Time: "+getStartTimeCookie);
                        if (((new Date).getMinutes() - getStartTimeCookie ) < 0 || ((new Date).getMinutes() - getStartTimeCookie ) >= 3 )  {
                            startTime = (new Date()).getMinutes();

                            $cookies.put("startTime", startTime, {expires: exp});
                            $cookies.put("lastUpdate", getCurrentDate(), {expires: exp});
                            $scope.lastRefresh = getCurrentDate();

                            var d = new Date(),
                                days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

                            if ( (d.getHours() >= 8 && d.getHours() <= 20) && !(days[d.getDay()] == "Sat" || days[d.getDay()] == "Sun") ) {
                                console.log("Refreshing data");
                                refreshTickers();
                            }
                            else
                            {
                                console.log( d.getHours()+", "+days[d.getDay()]+" - Afterhours. Do not refresh tickers.");
                            }
                        }
                        $timeout(p, interval);
                    })();
                }

                function refreshTickers() {
                    var url = "/refreshTickers";
                    var method = "POST";
                    var postData = "";

                    var shouldBeAsync = true;

                    var request = new XMLHttpRequest();

                    request.onload = function () {
                       var status = request.status; // HTTP response status, e.g., 200 for "200 OK"
                       var data = request.responseText; // Returned data, e.g., an HTML document.
                    }

                    request.open(method, url, shouldBeAsync);

                    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

                    request.send(postData);
                    $timeout($window.location.reload(true), 3000);
                }

                //Rate at which we check time for refresh
                $scope.pollData(5000);

                 $scope.checkStatus = function() {
                //    console.log("Checking status...");
                    (function checkStatusUpdate() {
                    $http.get('/status')
                        .then(function(response) {
                        //    console.log(response.data);
                            if (response.data['status'] == 'finished') {
                             $timeout($window.location.reload(true), 3000);
                            }
                        });
                    $timeout(checkStatusUpdate,2000);
                    })();
                }
                $scope.checkStatus(5000);

				$scope.showlist = function(){
                    $scope.loadComplete = false;
					$http({
						method: 'POST',
						url: '/getTickerList',

					}).then(function(response) {
						$scope.tickers = response.data;
						console.log('mm',$scope.tickers);

                        console.log("Load complete");

                        $scope.loadComplete = true;
					}, function(error) {
                        $scope.loadComplete = true;
						console.log(error);
					});
				}

				$scope.refreshTickers = function(){
                    $scope.loadComplete = false;
					$http({
						method: 'POST',
						url: '/refreshTickers',

					}).then(function(response) {
                        console.log("Refresh complete");
                        $scope.loadComplete = true;

                        $scope.showlist();
                        $scope.info = {}
					}, function(error) {
                        $scope.loadComplete = true;
						console.log(error);
					});
				}

				$scope.addTicker = function(){
					$http({
						method: 'POST',
						url: '/addTicker',
						data: {info:$scope.info}
					}).then(function(response) {
						$scope.showlist();
						$('#addPopUp').modal('hide')
						$scope.info = {}
                        console.log("Added.");
					}, function(error) {
						console.log(error);
					});
				}

                // This function is called when update button is clicked
				$scope.editTicker = function(id){
					$scope.info.id = id;

					$scope.showAdd = false;

					$http({
						method: 'POST',
						url: '/getTicker',
						data: {id:$scope.info.id}
					}).then(function(response) {
						console.log(response);
						$scope.info = response.data;
						$('#addPopUp').modal('show')
                        $window.document.getElementById("txtDevice").focus();
					}, function(error) {
						console.log(error);
					});
				}

				$scope.updateTicker = function(id){
					$http({
						method: 'POST',
						url: '/updateTicker',
						data: {info:$scope.info}
					}).then(function(response) {
						console.log(response.data);
						$scope.showlist();
						$('#addPopUp').modal('hide')

                        console.log("Updated.");
					}, function(error) {
						console.log(error);
					});
				}

                $scope.showStockTwits = function(tickerName){
                    window.open("https://stocktwits.com/symbol/"+tickerName+"?popout=true&substream=top", "newwindow", "width=800,height=600");
                }

				$scope.showTickerChart = function(tickerName){
					$scope.showChart = true;
                    $scope.tickerName = tickerName;
					$scope.info = {};
                    console.log($scope.tickerName);
					$('#displayChart').modal('show')
				}

				$scope.showAddPopUp = function(){
					$scope.showAdd = true;
					$scope.info = {};
					$('#addPopUp').modal('show')
                    $window.document.getElementById("txtDevice").focus();
				}

				$scope.showRunPopUp = function(id){
					$scope.info.id = id;
					$scope.run = {};

					$http({
						method: 'POST',
						url: '/getTicker',
						data: {id:$scope.info.id}
					}).then(function(response) {
						console.log(response);
						$scope.run = response.data;
						$scope.run.isRoot = false;
						$('#runPopUp').modal('show');
					}, function(error) {
						console.log(error);
					});
				}

				$scope.confirmDelete = function(id){
					$scope.deleteTickerId = id;
					$('#deleteConfirm').modal('show');
				}

				$scope.deleteTicker = function(){

					$http({
						method: 'POST',
						url: '/deleteTicker',
						data: {id:$scope.deleteTickerId}
					}).then(function(response) {
						console.log(response.data);
						$scope.deleteTickerId = '';
						$scope.showlist();
						$('#deleteConfirm').modal('hide')
					}, function(error) {
						console.log(error);
					});
				}

                $scope.showlist();
            })
