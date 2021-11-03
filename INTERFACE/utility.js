// IMGui port for making sure val is in range
function output_val_in_range(val, min, max, isLog, precision) {
  // assert(val >= 0 && val <= 1);
  logarithmic_zero_epsilon = Math.pow(0.367879441171, precision);
  output_linear = min + (val * abs(max - min));

  // Edge case for if max and min are flipped.
  if (max < min) {
    swap(min, max);
  }

  output = undefined;
  if (isLog) {
    min_linear = (abs(min) < logarithmic_zero_epsilon)
                           ? ((min < 0.0) ? -logarithmic_zero_epsilon : logarithmic_zero_epsilon)
                           : min;
    max_linear = (abs(max) < logarithmic_zero_epsilon)
                           ? ((max < 0.0) ? -logarithmic_zero_epsilon : logarithmic_zero_epsilon)
                           : max;

    if ((min == 0.0) && (max < 0.0))
      min_linear = -logarithmic_zero_epsilon;
    else if ((max == 0.0) && (min < 0.0))
      max_linear = -logarithmic_zero_epsilon;

    // Set output.
    if (output_linear < min_linear) {
      output = min;
    } else if (output_linear > max_linear) {
      output = max;
    } else if ((min * max) < 0.0) { // Range is in negative and positive.
      zero_point_center = (abs(min) / abs(max - min));
      if (val > zero_point_center - logarithmic_zero_epsilon &&
          val < zero_point_center +
                    logarithmic_zero_epsilon *
                        10) {               // hacky way to detect an equality with midi precision.
        output = 0.0;                      // Special case for exactly zero
      } else if (val < zero_point_center) { // val less than zero point (negative)
        min_log = Math.log(abs(min_linear));
        scale = (abs(min_log) - Math.log(logarithmic_zero_epsilon)) / (abs(min_linear));
        test = Math.log(logarithmic_zero_epsilon) + scale * abs(output_linear);
        output = -1 * Math.exp(Math.log(logarithmic_zero_epsilon) + scale * abs(output_linear));
      } else { // val less than zero point (positive)
        max_log = Math.log(max_linear);
        scale = (max_log - Math.log(logarithmic_zero_epsilon)) / (max_linear);
        output = Math.exp(Math.log(logarithmic_zero_epsilon) + scale * (output_linear));
      }
    } else if ((min < 0.0) || (max < 0.0)) { // Entirely negative slider
      v_min = Math.log(abs(min_linear));
      v_max = Math.log(abs(max_linear));
      scale = (v_min - v_max) / (min_linear - max_linear);
      output = -1 * Math.exp((v_min + scale * (output_linear - min_linear)));
    } else { // Entirely positive slider.
      v_min = Math.log(min_linear);
      v_max = Math.log(max_linear);
      scale = (v_max - v_min) / (max_linear - min_linear);
      output = Math.exp(v_max + scale * (output_linear - max_linear));
    }
  } else {
    output = output_linear;
  }

  return output;
}