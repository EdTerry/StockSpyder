        angular.module('myApp', [])
            .controller('HomeCtrl', function($scope, $http, $interval) {

				$scope.info = {};

				$scope.showAdd = true;
                $scope.loadComplete = false;
                $scope.refreshing = false;

                //Sorting
                $scope.orderByField = 'device';
                $scope.reverseSort = false;

                $scope.tickerName = "";

                //Used to test interval
                var testFunction = function(){
                    console.log("Testing!");
                }

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
                //Update every 5 minutes
                $interval($scope.refreshTickers, 300000);

				$scope.addTicker = function(){
					$http({
						method: 'POST',
						url: '/addTicker',
						data: {info:$scope.info}
					}).then(function(response) {
						$scope.showlist();
						$('#addPopUp').modal('hide')
						$scope.info = {}
					}, function(error) {
						console.log(error);
					});
				}

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
					}, function(error) {
						console.log(error);
					});
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

                $scope.refreshTickers();
            })
