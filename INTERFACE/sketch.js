//EVERYTHING IN LOCAL COORDS TILL ITS TIME TO DRAW
//DEVICE IS 1440 x 899
const dev_w = 1440;
const dev_h = 899;
const knob_w = 64;
const port_in = 12000; // osc port
const port_out = 57121;
const secondary_color = "#FFD300";

let bg_img;
let knobs;
let canv;
let winHeight;
let winWidth;
let socket; // osc
let latent_vis


function setWindowSize() {
    winHeight = min(windowHeight, dev_h * windowWidth / dev_w);
    winWidth = winHeight * dev_w / dev_h
}

function globalx(localx) {
    return localx * winWidth / dev_w;
}
function globaly(localy){
    return localy * winHeight / dev_h;
}
function localx(globalx) {
    return globalx * dev_w / winWidth;
}
function localy(globaly) {
    return globaly * dev_h / winHeight;
}

class Knob {
    constructor(name, x, y, w, h, min=0, max=127) {
        this.name = name;
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
        this.min_val = min;
        this.max_val = max;
        
        this.img = loadImage('IMG/knob.png');
        this.value = this.max_val/2;
        this.pressed = false;
        this.pressed_x;
        this.pressed_y;
        this.pressed_val;
        this.pixels_per_increment = 1.5; // num pixels mouse moves per increment
    }
    
    draw() {
        let x = globalx(this.x);
        let y = globaly(this.y);
        let w = globalx(this.w);
        let h = globaly(this.h);
        // draw knob from knob spritesheet
        image(this.img, x, y, w, h, knob_w*this.pos(), 0, knob_w, this.img.height);
        
        // draw text
        let fontsize = h/4;
        textSize(fontsize);
        textAlign(CENTER);
        textFont(font);
        strokeWeight(10);
        text(this.name, x + w/2, y + 1.5*fontsize + h);
    }
    
    pos() {
        return Math.round(63*(this.value - this.min_val) / (this.max_val - this.min_val));
    }
    
    collision(x, y) { //x and y in local coordinates
        return x < this.x + this.w && x > this.x && y > this.y && y < this.y + this.h; 
    }
    
    press(x, y) { // press knob at x, y in local coords
        this.pressed = true;
        this.pressed_x = x;
        this.pressed_y = y;
        this.pressed_val = this.value;
    }
    
    update() { // mouse_x and mouse_y mouse position in global coords
        if (this.pressed) {
            let d = mouseX - globalx(this.pressed_x) - mouseY + globaly(this.pressed_y);
            this.value = this.pressed_val + d / this.pixels_per_increment;
            this.value = constrain(this.value, this.min_val, this.max_val);
        }
    }
    
    release() {
        this.pressed = false;
    }
}

class LatentVisualizer {
    constructor(screen, model, x, y, w, h) {
        this.screen = screen;
        this.model = model;
        this.x = x;
        this.y = y;
        this.h = h;
        this.w = w;
        this.pca_x = 0;
        this.pca_y = 0;
        this.line_w = 10;
        
        this.pressed = false;
    }
    
    draw() {
        this.screen.scale(1*winWidth / dev_w);
        this.screen.rotateX(frameCount * 0.01);
        this.screen.rotateY(frameCount * 0.01);
        this.screen.normalMaterial();
        this.screen.model(this.model);
        image(this.screen, globalx(this.x), globaly(this.y), globalx(this.w), globaly(this.h));
        this.screen.clear();
        this.screen.reset();

        // draw markers of position
        strokeWeight(10);
        let pca_x_draw = this.line_w/2 + globalx(this.x) + 
                        (globalx(this.w) - this.line_w)*(this.pca_x + 1)/2
        let pca_y_draw = this.line_w/2 + globaly(this.y) + 
                        (globaly(this.h) - this.line_w)*(this.pca_y + 1)/2
        line(pca_x_draw - globalx(this.line_w/2), 
                globaly(this.y + this.h), 
                pca_x_draw + globalx(this.line_w/2), 
                globaly(this.y + this.h));
        line(globalx(this.x), 
                pca_y_draw - globaly(this.line_w/2), 
                globalx(this.x),  
                pca_y_draw + globaly(this.line_w/2));
    }
    
    collision(x, y) { //x and y in local coordinates
        return x < this.x + this.w && x > this.x && y > this.y && y < this.y + this.h; 
    }
    
    press(x, y) { // press knob at x, y in local coords
        this.pressed = true;
    }
    
    update() { // mouse_x and mouse_y mouse position in global coords
        if (this.pressed) {
            this.pca_x = 2*(mouseX - globalx(this.x))/globalx(this.w) - 1;
            this.pca_y = 2*(mouseY - globaly(this.y))/globaly(this.w) - 1;
            this.pca_x = constrain(this.pca_x, -1, 1);
            this.pca_y = constrain(this.pca_y, -1, 1);
        }
    }
    
    release() {
        this.pressed = false;
    }
}


function preload(){
    bg_img = loadImage("./IMG/Layout.png")
    // load font
    font = loadFont("./FONT/photonica_regular.ttf");
    
    // load 3D model
    compass = loadModel('./3D/compass.obj', true);
    
}

function setup() {
    setWindowSize();
    canv = createCanvas(winWidth, winHeight);
    canv.center();
    compass_screen = createGraphics(globalx(507), globaly(507), WEBGL); // 507 is width of miniscreen
    
    // create knobs
    knobs = [new Knob("spread", 903-knob_w/2,512, 64, 64), 
            new Knob("voices", 903 - knob_w/2,640, 64, 64),
            new Knob("attack", 1169 - 310/4 - knob_w/2,512, 64, 64),
            new Knob("decay", 1169 + 310/4 - knob_w/2,512, 64, 64),
            new Knob("sustain", 1169 - 310/4 - knob_w/2,640, 64, 64),
            new Knob("release", 1169 + 310/4 - knob_w/2,640, 64, 64)]
    
    
    latent_vis = new LatentVisualizer(compass_screen, compass, 130, 252, 507, 507);
    
    stroke(secondary_color);

    setupOsc(port_in, port_out);
}

function draw() {
    background(bg_img);
    for (knob of knobs) {
        knob.draw();
    }
    latent_vis.draw();
    sendOsc("/1/xy1/", 1)
}

function mousePressed() {
    x = localx(mouseX);
    y = localy(mouseY);
    for (knob of knobs) {
        if (knob.collision(x, y)) {
            knob.press(x, y);
        }
    }
    if (latent_vis.collision(x, y)) {
        latent_vis.press(x, y);
    }
}

function mouseDragged() {
    for (knob of knobs) {
        knob.update();
    }
    latent_vis.update();
}

function mouseReleased() {
    for (knob of knobs) {
        knob.release();
    }
    latent_vis.release();
}

function windowResized() {
    setWindowSize();
    resizeCanvas(winWidth, winHeight);
    canv.center();
    compass_screen.resizeCanvas(globalx(507), globaly(507));
}

https://github.com/genekogan/p5js-osc/blob/master/p5-basic/sketch.js
function receiveOsc(address, value) {
    console.log("received OSC: " + address + ", " + value);

    if (address == '/test') {
        x = value[0];
        y = value[1];
    }
}

function sendOsc(address, value) {
    socket.emit('message', [address].concat(value));
}

function setupOsc(oscPortIn, oscPortOut) {
    socket = io.connect('http://127.0.0.1:8080', { port: 57121, rememberTransport: false });
    socket.on('connect', function() {
        socket.emit('config', {
            server: { port: oscPortIn,  host: '127.0.0.1'},
            client: { port: oscPortOut, host: '127.0.0.1'}
        });
    });
    socket.on('message', function(msg) {
        if (msg[0] == '#bundle') {
            for (var i=2; i<msg.length; i++) {
                receiveOsc(msg[i][0], msg[i].splice(1));
            }
        } else {
            receiveOsc(msg[0], msg.splice(1));
        }
    });
}