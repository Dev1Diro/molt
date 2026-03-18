// The existing content of the index.js file should be included here along with the following new additions:

// Async function to generate comments using the Grok API
async function generateComment(post_id) {
    // Call to Grok API to generate witty comments
    const response = await fetch(`https://api.grok.com/generate?post_id=${post_id}`);
    const data = await response.json();
    return data.comment;
}

// POST endpoint for creating a comment
app.post('/comment', async (req, res) => {
    const { post_id } = req.body;
    if (!post_id) {
        return res.status(400).send('post_id is required');
    }
    try {
        const comment = await generateComment(post_id);
        // Logic to save the comment in your database should be added here
        res.status(201).send({ comment });
    } catch (error) {
        res.status(500).send('Error generating comment');
    }
});

// Make sure to maintain the existing 30-minute post cycle logic here.