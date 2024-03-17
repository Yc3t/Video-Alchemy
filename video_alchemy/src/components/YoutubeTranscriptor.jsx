import React, { useState } from 'react';
import axios from 'axios';

const YoutubeTranscriptEditor = () => {
  const [videoUrl, setVideoUrl] = useState('');
  const [status, setStatus] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('Processing...');

    try {
      // Call the backend API to process the video
      await axios.post('http://localhost:5000/api/process-video', { videoUrl });
      setStatus('Video processed successfully!');
    } catch (error) {
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        setStatus(`Error: ${error.response.data.error}`);
      } else if (error.request) {
        // The request was made but no response was received
        setStatus('Error: No response from the server');
      } else {
        // Something happened in setting up the request that triggered an Error
        setStatus('Error: Something went wrong');
      }
    }
  };

  return (
    <div>
      <h1>YouTube Transcript Editor</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter YouTube video URL"
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.target.value)}
        />
        <button type="submit">Process Video</button>
      </form>
      <p>{status}</p>
    </div>
  );
};

export default YoutubeTranscriptEditor;
