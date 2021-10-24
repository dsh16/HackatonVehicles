<template>
  <div class="home">
    <!-- header -->
    <header>
      <el-menu
       background-color="#407294"
        text-color="white"
        active-text-color="white"
        :default-active="activeIndex"
        class="el-menu-demo"
        mode="horizontal"
        @select="handleSelect"
      >
        <el-menu-item index="1"><router-link to="/">Главная страница</router-link></el-menu-item>
        <el-menu-item index="2"><router-link to="analytics">Аналитика</router-link></el-menu-item>
        <el-menu-item index="3">О проекте</el-menu-item>
      </el-menu>
    </header>

    <router-view />

    <!-- footer -->
    <!-- <footer>

    </footer> -->
  </div>
</template>

<style scoped>
@import url(https://use.fontawesome.com/releases/v5.15.2/css/all.css);
@import url(https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap);
</style>

<script>
import axios from "axios";
import { mapGetters, mapMutations } from "vuex";
import { defineComponent, ref } from "vue";
export default {
  name: "Layout",
  components: {},
  data() {
    return {
      currentWeatherLayout: null,
  temp: null
    };
  },
  setup() {
    const activeIndex = ref("1");
    const activeIndex2 = ref("1");
    const handleSelect = (key, keyPath) => {
      console.log(key, keyPath);
    };
    return {
      activeIndex,
      activeIndex2,
      handleSelect,
    };
  },
  mounted() {
    axios
      .get(
        "http://api.openweathermap.org/data/2.5/weather?q=Lipetsk&lang=ru&units=metric&appid=fd965aaa128624a747e3ff8c08b58442"
      )
      .then((response) => {
        this.currentWeatherLayout = response,
         this.snow = this.currentWeatherLayout.data.snow
      });
     ;
  },

   

};
</script>


<style scoped>
.el-menu{
  box-shadow: 4px 4px 8px 0px rgba(9, 14, 17, 0.2);
}
.info{
  display: flex;
  align-content: center;
  justify-content: center;
  width: 100%;
}
</style>
