// document.addEventListener("DOMContentLoaded", function() {
//   const button = document.getElementById("plot-button");
//   button.addEventListener("click", plotChart);
//
//   let chart;
var chart;
function plotChart() {
  console.log("OHAI");
  // Get data from the text file
  fetch("data.txt")
    .then(response => response.text())
    .then(data => {
      // Parse the data
      const lines = data.trim().split("\n");
      const labels = [];
      const values = [];

      for (const line of lines) {
        const [label, value] = line.split(",");
        labels.push(Number(label));
        values.push(Number(value));
      }



      // This is for assigning colours to specific bars:
      var colors = Array(labels.length).fill('rgba(75, 192, 192, 0.6)');
      var bcolors = Array(labels.length).fill('rgba(75, 192, 192, 1)');

      var labelColors = {
        3: 'rgba(192, 75, 192, 0.6)',
        5: 'rgba(192, 75, 192, 0.6)'
      };
      var labelbColors = {
        3: 'rgba(192, 75, 192, 1)',
        5: 'rgba(192, 75, 192, 1)'
      };
      for (var i = 0; i < labels.length; i++) {
        var label = labels[i];
        if (labelColors.hasOwnProperty(label)) {
          colors[i] = labelColors[label];
          bcolors[i] = labelbColors[label];
        }
      }
      // End colouring


      // Check if a chart already exists, destroy it if yes
      if (chart) {
        chart.data.labels = labels;
        chart.data.datasets[0].data = values;
        chart.update();
      } else {
      // Create a new chart
        const ctx = document.getElementById("chart").getContext("2d");
        chart = new Chart(ctx, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [
              {
                label: "Amazing Data",
                data: values,
                backgroundColor: colors,
                borderColor: bcolors,
                borderWidth: 1
              }
            ]
          },
          options: {
            responsive: true,
            scales: {
              y: {
                beginAtZero: true
              }
            }
          }
        });
      }
    })
    .catch(error => {
      console.log("Error:", error);
    });
};


plotChart();
// });
