package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
)

type Config struct {
	Latitude      float64            `json:"latitude"`
	Longitude     float64            `json:"longitude"`
	SearchRadius  int                `json:"search_radius"`
	SatColorPairs map[string]string  `json:"sat_color_pairs"`
}

func main() {
	file, _ := os.Open("config.json")
	defer file.Close()

	var config Config
	json.NewDecoder(file).Decode(&config)

	params := url.Values{}
	params.Add("lat", fmt.Sprintf("%f", config.Latitude))
	params.Add("lng", fmt.Sprintf("%f", config.Longitude))
	params.Add("search_radius", fmt.Sprintf("%d", config.SearchRadius))
	satColorPairs := []string{}
	for id, color := range config.SatColorPairs {
		satColorPairs = append(satColorPairs, fmt.Sprintf("%s,%s", id, color))
	}
	params.Add("sat_color_pairs", strings.Join(satColorPairs, ","))
	params.Add("format", "text")

	apiURL := "https://revontulet.lol/api/satellites/above/stream?" + params.Encode()
	resp, _ := http.Get(apiURL)
	defer resp.Body.Close()

	scanner := bufio.NewScanner(resp.Body)
	for scanner.Scan() {
		fmt.Println(scanner.Text())
	}
}
