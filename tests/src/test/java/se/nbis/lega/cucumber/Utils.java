package se.nbis.lega.cucumber;

import com.github.dockerjava.api.DockerClient;
import com.github.dockerjava.api.command.CreateContainerResponse;
import com.github.dockerjava.api.model.AccessMode;
import com.github.dockerjava.api.model.Bind;
import com.github.dockerjava.api.model.Container;
import com.github.dockerjava.api.model.Volume;
import com.github.dockerjava.core.DefaultDockerClientConfig;
import com.github.dockerjava.core.DockerClientBuilder;
import com.github.dockerjava.core.command.ExecStartResultCallback;
import com.github.dockerjava.core.command.WaitContainerResultCallback;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang.ArrayUtils;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Paths;

/**
 * Utility methods for the test-suite.
 */
public class Utils {

    private DockerClient dockerClient;

    /**
     * Public constructor with Docker client initialization.
     */
    public Utils() {
        this.dockerClient = DockerClientBuilder.getInstance(DefaultDockerClientConfig.createDefaultConfigBuilder().build()).build();
    }

    /**
     * Executes shell command within specified container.
     *
     * @param container Container to execute command in.
     * @param command   Command to execute.
     * @return Command output.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the command execution is interrupted.
     */
    public String executeWithinContainer(Container container, String... command) throws IOException, InterruptedException {
        String execId = dockerClient.
                execCreateCmd(container.getId()).
                withCmd(command).
                withAttachStdout(true).
                withAttachStderr(true).
                exec().
                getId();
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        ExecStartResultCallback resultCallback = new ExecStartResultCallback(outputStream, System.err);
        dockerClient.execStartCmd(execId).exec(resultCallback);
        resultCallback.awaitCompletion();
        return new String(outputStream.toByteArray());
    }

    /**
     * Executes PSQL query.
     *
     * @param query Query to execute.
     * @return Query output.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public String executeDBQuery(String query) throws IOException, InterruptedException {
        return executeWithinContainer(findContainer("nbis/ega:db", "ega_db"), "psql", "-U", readTraceProperty("DB_USER"), "-d", "lega", "-c", query);
    }

    /**
     * Spawns "nbis/ega:worker" container, mounts data folder there and executes a command.
     *
     * @param from  Folder to mount from.
     * @param to  Folder to mount to.
     * @param command Command to execute.
     * @throws InterruptedException In case the command execution is interrupted.
     */
    public void spawnWorkerAndExecute(String from, String to, String... command) throws InterruptedException {
        Volume dataVolume = new Volume(to);
        Volume gpgVolume = new Volume("/root/.gnupg");
        CreateContainerResponse createContainerResponse = dockerClient.
                createContainerCmd("nbis/ega:worker").
                withVolumes(dataVolume, gpgVolume).
                withBinds(new Bind(from, dataVolume),
                        new Bind(Paths.get("").toAbsolutePath().getParent().toString() + "/docker/bootstrap/private/gpg", gpgVolume, AccessMode.ro)).
                withCmd(command).
                exec();
        dockerClient.startContainerCmd(createContainerResponse.getId()).exec();
        WaitContainerResultCallback resultCallback = new WaitContainerResultCallback();
        dockerClient.waitContainerCmd(createContainerResponse.getId()).exec(resultCallback);
        resultCallback.awaitCompletion();
        dockerClient.removeContainerCmd(createContainerResponse.getId()).exec();
    }

    /**
     * Reads property from the trace file.
     *
     * @param property Property name.
     * @return Property value.
     * @throws IOException In case it's not possible to read trace file.
     */
    public String readTraceProperty(String fileName, String property) throws IOException {
        File trace = new File(Paths.get("").toAbsolutePath().getParent().toString() + "/docker/private/" + fileName);
        return FileUtils.readLines(trace, Charset.defaultCharset()).
                stream().
                filter(l -> l.startsWith(property)).
                map(p -> p.split(" = ")[1]).
                findAny().orElse(null);
    }

    /**
     * Finds container by image name and container name.
     *
     * @param imageName     Image name.
     * @param containerName Container name.
     * @return Docker container.
     */
    public Container findContainer(String imageName, String containerName) {
        return dockerClient.listContainersCmd().exec().
                stream().
                filter(c -> c.getImage().equals(imageName)).
                filter(c -> ArrayUtils.contains(c.getNames(), "/" + containerName)).
                findAny().
                orElse(null);
    }

    /**
     * Calculates MD5 hash of a file.
     *
     * @param file File to calculate hash for.
     * @return MD5 hash.
     * @throws IOException In case it's not possible ot read the file.
     */
    public String calculateMD5(File file) throws IOException {
        FileInputStream fileInputStream = new FileInputStream(file);
        String md5 = DigestUtils.md5Hex(fileInputStream);
        fileInputStream.close();
        return md5;
    }

    public DockerClient getDockerClient() {
        return dockerClient;
    }

}
