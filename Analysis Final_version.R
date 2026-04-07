# 1. ENTERING DATA
audio_time     <- c(50, 44, 63, 43, 41, 44, 60, 70, 93, 55, 160, 50)
audio_accuracy <- c(75.00, 63.16, 64.71, 62.50, 64.71, 66.67,
                    57.14, 29.41, 34.48, 68.75, 34.29, 92.31)

visual_time     <- c(79, 32, 41, 54, 54, 53, 105, 70, 56, 102, 64, 98)
visual_accuracy <- c(75.00, 76.92, 58.82, 54.55, 66.67, 64.71,
                     54.55, 52.63, 55.00, 27.91, 55.00, 55.00)

my_data <- data.frame(
  feedback = factor(c(rep("Audio", 12), rep("Visual", 12))),
  time     = c(audio_time,     visual_time),
  accuracy = c(audio_accuracy, visual_accuracy)
)

#  2. DESCRIPTIVE STATISTICS 
cat("=== Descriptive Statistics ===\n")
aggregate(cbind(time, accuracy) ~ feedback, data = my_data,
          FUN = function(x) round(c(mean = mean(x), sd = sd(x),
                                    min = min(x),  max = max(x)), 2))
# Combined stats
cat("=== Combined Stats ===\n")
combined_stats <- data.frame(
  Dependent_Variable = c("Completion Time (s)", "Accuracy (%)"),
  Mean = round(c(mean(my_data$time), mean(my_data$accuracy)), 2),
  SD   = round(c(sd(my_data$time),   sd(my_data$accuracy)),   2),
  Min  = round(c(min(my_data$time),  min(my_data$accuracy)),  2),
  Max  = round(c(max(my_data$time),  max(my_data$accuracy)),  2)
)
print(combined_stats)

# 3. BOXPLOTS 
my_data_combined <- rbind(my_data, 
                          data.frame(feedback = factor("Combined"), 
                                     time     = my_data$time, 
                                     accuracy = my_data$accuracy))

my_data_combined$feedback <- factor(my_data_combined$feedback, 
                                    levels = c("Audio", "Visual", "Combined"))

par(mfrow = c(1, 2))
#Time
boxplot(time ~ feedback, data = my_data_combined,
        main = "Task Completion Time\nby Feedback Type",
        ylab = "Time (seconds)",
        xlab = "Feedback Type",
        col  = c("#AFA9EC", "#5DCAA5", "#AFA9EC"))
# Accuracy
boxplot(accuracy ~ feedback, data = my_data_combined,
        main = "Adjusted Accuracy\nby Feedback Type",
        ylab = "Adjusted Accuracy (%)",
        xlab = "Feedback Type",
        col  = c("#AFA9EC", "#5DCAA5", "#AFA9EC"))
par(mfrow = c(1, 1))
# 4. TWO-SAMPLE WELCH T-TESTS 
cat("\n=== t-test: TIME ===\n")
t_time <- t.test(time ~ feedback, data = my_data,
                 alternative = "two.sided", var.equal = FALSE)
print(t_time)

cat("\n=== t-test: ACCURACY ===\n")
t_acc <- t.test(accuracy ~ feedback, data = my_data,
                alternative = "two.sided", var.equal = FALSE)
print(t_acc)

# 6. PEARSON CORRELATION (speed-accuracy tradeoff) 
cat("\n=== Pearson Correlation: Time vs Accuracy ===\n")
cor_result <- cor.test(my_data$time, my_data$accuracy, method = "pearson")
print(cor_result)

# Scatter plot with regression line
par(mfrow = c(1, 1))
plot(my_data$time, my_data$accuracy,
     col  = ifelse(my_data$feedback == "Audio", "#534AB7", "#0F6E56"),
     pch  = 19, cex = 1.2,
     xlab = "Time (seconds)",
     ylab = "Adjusted Accuracy (%)",
     main = "Speed-Accuracy Tradeoff")
abline(lm(accuracy ~ time, data = my_data), lty = 2, col = "gray40")
legend("topright", legend = c("Audio", "Visual"),
       col = c("#534AB7", "#0F6E56"), pch = 19)

# 7. NORMALITY CHECKS
cat("\n=== Normality Tests ===\n")

cat("\nAudio — Time:\n");       print(shapiro.test(audio_time))
cat("\nVisual — Time:\n");      print(shapiro.test(visual_time))
cat("\nAudio — Accuracy:\n");   print(shapiro.test(audio_accuracy))
cat("\nVisual — Accuracy:\n");  print(shapiro.test(visual_accuracy))

# QQ plots
par(mfrow = c(2, 2))
qqnorm(audio_time,      main = "Q-Q: Audio Time");      qqline(audio_time)
qqnorm(audio_accuracy,  main = "Q-Q: Audio Accuracy");  qqline(audio_accuracy)
qqnorm(visual_time,     main = "Q-Q: Visual Time");     qqline(visual_time)
qqnorm(visual_accuracy, main = "Q-Q: Visual Accuracy"); qqline(visual_accuracy)
par(mfrow = c(1, 1))

#8. RERUN ANALYSIS WITHOUT OUTLIER
my_data_clean <- my_data[my_data$time != 160, ]

# Rerun Shapiro-Wilk
audio_time_c  <- my_data_clean$time[my_data_clean$feedback == "Audio"]
visual_time_c <- my_data_clean$time[my_data_clean$feedback == "Visual"]
audio_acc_c   <- my_data_clean$accuracy[my_data_clean$feedback == "Audio"]
visual_acc_c  <- my_data_clean$accuracy[my_data_clean$feedback == "Visual"]

cat("\nAudio — Time:\n");      print(shapiro.test(audio_time_c))
cat("\nVisual — Time:\n");     print(shapiro.test(visual_time_c))
cat("\nAudio — Accuracy:\n");  print(shapiro.test(audio_acc_c))
cat("\nVisual — Accuracy:\n"); print(shapiro.test(visual_acc_c))

# QQ plots with (160s) removed, n=23
par(mfrow = c(2, 2))

qqnorm(audio_time_c,  main = "Q-Q: Audio Time without Outlier");     qqline(audio_time_c)
qqnorm(audio_acc_c,   main = "Q-Q: Audio Accuracy without Outlier"); qqline(audio_acc_c)
qqnorm(visual_time_c, main = "Q-Q: Visual Time without Outlier");    qqline(visual_time_c)
qqnorm(visual_acc_c,  main = "Q-Q: Visual Accuracy without Outlier");qqline(visual_acc_c)

# Rerun t-tests
t.test(time ~ feedback, data = my_data_clean,
       alternative = "two.sided", var.equal = FALSE)
t.test(accuracy ~ feedback, data = my_data_clean,
       alternative = "two.sided", var.equal = FALSE)
