<template>
  <div class="home">
    <div class="side">
      <div class="top">
        <div class="switch">
          <el-switch
            v-model="value2"
            style="display: block"
            active-color="#13ce66"
            inactive-color="#ff4949"
            active-text="Автоматический расчет"
            inactive-text="Ручной ввод"
          />
        </div>
        <div class="switch-info" v-if="value2">
          {{ temp }}
        </div>
        <div class="switch-info" v-if="!value2">
          <label>Введите количество осадков (в мм):</label>
          <el-input
            v-model="mm"
            placeholder="Количество осадков в мм"
          ></el-input>
          <el-input
            v-model="cars"
            placeholder="Количество доступных для работы машин"
          ></el-input>
          <el-button type="primary" v-on:click="randomGeo()"
            >Смоделировать маршрут</el-button
          >
        </div>
        <div
          v-if="temp === 'Снега в городе не было за последние 3 часа' && value2"
        >
          <el-button disabled type="primary">Смоделировать маршрут</el-button>
        </div>
      </div>
      <div class="bottom">
        <el-button type="danger" class="complaint" @click="dialogVisible = true"
          >Подать жалобу</el-button
        >
      </div>
    </div>
    <div id="mapContainer"></div>

    <el-dialog
      v-model="dialogVisible"
      title="Подать жалобу"
      width="30%"
      :before-close="handleClose"
    >
      <span></span>
      <label> Укажите свой email для обратной связи </label>
      <el-input v-model="email" placeholder="Email"></el-input>
      <el-input
        class="area"
        v-model="complaint"
        :autosize="{ minRows: 2, maxRows: 4 }"
        type="textarea"
        placeholder="Введите текст обращения"
      >
      </el-input>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Отмена</el-button>
          <el-button type="primary" @click="dialogVisible = false"
            >Отправить</el-button
          >
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
// @ is an alias tcdco /src
import HelloWorld from "@/components/HelloWorld.vue";
import "leaflet/dist/leaflet.css";
import "leaflet-routing-machine/dist/leaflet-routing-machine.css";
import axios from "axios";
import L from "leaflet";

import MapboxDraw from "@mapbox/mapbox-gl-draw";

require("leaflet-routing-machine");
require("lrm-graphhopper");

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: require("leaflet/dist/images/marker-icon-2x.png"),
  iconUrl: require("leaflet/dist/images/marker-icon.png"),
  shadowUrl: require("leaflet/dist/images/marker-shadow.png"),
});
export default {
  name: "Home",
  components: {
    HelloWorld,
  },
  data() {
    return {
      email: null,
      complaint: null,
      dialogVisible: false,
      mm: null,
      cars: null,
      value1: true,
      value2: true,
      currentWeather: null,
      temp: null,
      center: [37, 7749, -122, 4194],
      mapDiv: null,
    };
  },
  methods: {
    randomGeo: function () {
      const mapDiv = this.mapDiv;
      function getRandomInRange(from, to, fixed) {
        return (Math.random() * (to - from) + from).toFixed(fixed) * 1;
        // .toFixed() returns string, so ' * 1' is a trick to convert to number
      }
      for (var i = 0; i < this.cars; i++) {
        L.Routing.control({
          waypoints: [
            L.latLng(52.617551, 39.5284553),
            L.latLng(
              getRandomInRange(52.6215126, 52.5831049, 6),
              getRandomInRange(39.5204083, 39.5989621, 6)
            ),
          ],
        }).addTo(mapDiv);
      }
    },

    // showRoutes: function () {
    //   function getRandomInRange(from, to, fixed) {
    //     return (Math.random() * (to - from) + from).toFixed(fixed) * 1;
    //     // .toFixed() returns string, so ' * 1' is a trick to convert to number
    //   }
    //   const mapDiv = this.mapDiv;
    //   L.Routing.control({
    //     waypoints: [
    //       L.latLng(52.617551, 39.5284553),
    //       L.latLng(52.6035553, 39.5773054),
    //     ],
    //   }).addTo(mapDiv);
    //   L.Routing.control({
    //     waypoints: [
    //       L.latLng(52.617551, 39.5284553),
    //       L.latLng(52.5957808, 39.5587401),
    //     ],
    //   }).addTo(mapDiv);
    //   L.Routing.control({
    //     waypoints: [
    //       L.latLng(52.617551, 39.5284553),
    //       L.latLng(52.5965456, 39.5415067),
    //     ],
    //   }).addTo(mapDiv);
    //   L.Routing.control({
    //     waypoints: [
    //       L.latLng(52.617551, 39.5284553),
    //       L.latLng(52.5854776, 39.5693839),
    //     ],
    //   }).addTo(mapDiv);
    //   L.Routing.control({
    //     waypoints: [
    //       L.latLng(52.617551, 39.5284553),
    //       L.latLng(52.6123284, 39.5638182),
    //     ],
    //   }).addTo(mapDiv);
      
    // },
    setupLeafletMap: function () {
      const mapDiv = L.map("mapContainer").setView([52.6042, 39.5938], 13);
      this.mapDiv = mapDiv;
      L.tileLayer(
        "https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}",
        {
          attribution:
            'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
          maxZoom: 18,
          id: "dsh16/ckv3ennau4mvn14qkxgtw8clm",
          tileSize: 512,
          zoomOffset: -1,
          accessToken:
            "pk.eyJ1IjoiZHNoMTYiLCJhIjoiY2t2M2Q5OHU2MGxoaDJ1czMxaGs0dW03NSJ9.5nyAAHMveJrg5uL46uFVvQ",
        }
      ).addTo(mapDiv);

      var greenIcon = L.icon({
        iconUrl: require("@/assets/garage.png"),
        iconSize: [40, 40], // size of the icon
        popupAnchor: [-3, -76], // point from which the popup should open relative to the iconAnchor
      });
      L.marker([52.617551, 39.5284553], { icon: greenIcon }).addTo(mapDiv);
      this.mapDiv = mapDiv;
    },
  },
  mounted() {
    this.$nextTick(function () {
      axios
        .get(
          "http://api.openweathermap.org/data/2.5/weather?q=Lipetsk&lang=ru&units=metric&appid=fd965aaa128624a747e3ff8c08b58442"
        )
        .then((response) => {
          (this.currentWeather = response),
            (this.temp =
              this.currentWeather.data.snow !== undefined
                ? this.currentWeather.data.snow
                : "Снега в городе не было за последние 3 часа");
          this.setupLeafletMap();
        });
    });
  },
};
</script>

<style scoped>
@import url(https://use.fontawesome.com/releases/v5.15.2/css/all.css);
@import url(https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;700&display=swap);

.dialog-footer > .el-button {
  margin: 0px;
  margin-left: 15px;
}
.area {
  margin-top: 15px;
}
.home {
  background-color: aliceblue;
  display: flex;
  font-family: "Montserrat";
}

.bottom {
  padding: 0px 10px;
}
.complaint {
  width: 90%;
}
.el-input {
  padding-top: 10px;
}
.switch-info {
  padding-top: 20px;
}
.el-button {
  margin: 20px;
}
.side {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  flex-direction: column;
  width: 370px;
}
.switch {
  display: flex;
  align-items: center;
  justify-content: center;
}
#mapContainer {
  margin: auto;
  width: 80vw;
  height: 90vh;
}
</style>