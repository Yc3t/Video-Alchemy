const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

app.post('/api/process-video', (req, res) => {
  const { videoUrl, quality } = req.body;

  if (!videoUrl) {
    res.status(400).json({
      error: 'Video URL is required.',
    });
    return;
  }

  const getTranscript = spawn('python', ['scripts/get_transcript.py', videoUrl, quality]);

  let getTranscriptError = '';

  getTranscript.stdout.on('data', (data) => {
    console.log(`get_transcript.py: ${data}`);
  });

  getTranscript.stderr.on('data', (data) => {
    console.error(`get_transcript.py error: ${data}`);
    getTranscriptError += data.toString();
  });

  getTranscript.on('close', (code) => {
    console.log(`get_transcript.py exited with code ${code}`);

    if (code === 0) {
      const videoIdMatch = videoUrl.match(/(?:v=|\/|embed\/|shorts\/|v\/|e\/|watch\?v=|\&v=)([^#\&\?]*)/);
      
      if (videoIdMatch && videoIdMatch[1]) {
        const videoId = videoIdMatch[1];
        const videoDir = path.join(__dirname, 'videos', videoId);
        const transcriptFile = path.join(videoDir, `${videoId}_transcript.vtt`);
        const importantMomentsFile = path.join(videoDir, 'important_moments.txt');

        const getImportantMoments = spawn('python', [
          'scripts/get_important_moments.py',
          transcriptFile,
          importantMomentsFile,
          '01:00:00.000',
          '02:00:00.000',
        ]);

        let getImportantMomentsError = '';

        getImportantMoments.stdout.on('data', (data) => {
          console.log(`get_important_moments.py: ${data}`);
        });

        getImportantMoments.stderr.on('data', (data) => {
          console.error(`get_important_moments.py error: ${data}`);
          getImportantMomentsError += data.toString();
        });

        getImportantMoments.on('close', (code) => {
          console.log(`get_important_moments.py exited with code ${code}`);

          if (code === 0) {
            const videoFile = path.join(videoDir, `${videoId}.mp4`);
            const outputFile = path.join(videoDir, 'output');
            const wordBoundaryFile = path.join(videoDir, `${videoId}_transcript_word_timestamps.txt`);

            const createMovie = spawn('python', [
              'scripts/create_movie.py',
              videoFile,
              outputFile,
              importantMomentsFile,
              wordBoundaryFile,
            ]);

            let createMovieError = '';

            createMovie.stdout.on('data', (data) => {
              console.log(`create_movie.py: ${data}`);
            });

            createMovie.stderr.on('data', (data) => {
              console.error(`create_movie.py error: ${data}`);
              createMovieError += data.toString();
            });

            createMovie.on('close', (code) => {
              console.log(`create_movie.py exited with code ${code}`);

              if (code === 0) {
                res.json({
                  message: 'Video processed successfully!',
                  outputFile: outputFile,
                });
              } else {
                res.status(500).json({
                  error: 'An error occurred while creating the movie.',
                  details: createMovieError,
                });
              }
            });
          } else {
            res.status(500).json({
              error: 'An error occurred while getting important moments.',
              details: getImportantMomentsError,
            });
          }
        });
      } else {
        res.status(400).json({
          error: 'Invalid video URL. Unable to extract video ID.',
        });
      }
    } else {
      res.status(500).json({
        error: 'An error occurred while getting the transcript.',
        details: getTranscriptError,
      });
    }
  });
});

app.use('/videos', express.static(path.join(__dirname, 'videos')));

const port = process.env.PORT || 5000;
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
