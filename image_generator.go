package main

import (
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"log"
	"net/http"
)

type Gene struct {
	Chromosome string
	End        int
	Key        string
	Orthologs  bool
	Siblings   []string
	start      int
	value      int
}

// type Chromosome struct {
// 	Data []Gene
// }

func main() {

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		var c []Gene
		err := json.NewDecoder(r.Body).Decode(&c)
		if err != nil {
			log.Fatal(err)
		}
		for i := 0; i < len(c); i++ {
			fmt.Println(c[i].Key)
		}
		// fmt.Println(c[0])
		fmt.Fprintf(w, "Testing!")

		width := 200
		height := 100

		upLeft := image.Point{0, 0}
		lowRight := image.Point{width, height}

		img := image.NewRGBA(image.Rectangle{upLeft, lowRight})

		// Colors are defined by Red, Green, Blue, Alpha uint8 values.
		cyan := color.RGBA{100, 200, 200, 0xff}

		// Set color for each pixel.
		for x := 0; x < width; x++ {
			for y := 0; y < height; y++ {
				switch {
				case x < width/2 && y < height/2: // upper left quadrant
					img.Set(x, y, cyan)
				case x >= width/2 && y >= height/2: // lower right quadrant
					img.Set(x, y, color.White)
				default:
					// Use zero value.
				}
			}
		}

		// Encode as PNG.
		// f, _ := os.Create("image.png")
		w.Header().Set("Content-Type", "image/png")
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type,access-control-allow-origin, access-control-allow-headers")
		// w.Write(img)
		png.Encode(w, img)

	})

	fmt.Printf("Starting server at port 8080\n")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}
