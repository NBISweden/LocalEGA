package no.uio.ifi.lega.cucumber.steps;

import cucumber.api.java.Before;
import cucumber.api.java8.En;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.sftp.SFTPClient;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;
import org.junit.Assert;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;

public class Authentication implements En {

    private String username;
    private String password;

    private SFTPClient sftp;

    @Before
    public void setUp() throws IOException {
        File users = new File("../docker/bootstrap/private/cega/users");
        File user = FileUtils.listFiles(users, new String[]{"yml"}, false).iterator().next();
        username = FilenameUtils.getBaseName(user.getName());
        File trace = new File("../docker/bootstrap/private/.trace");
        password = FileUtils.readLines(trace, Charset.defaultCharset()).
                stream().
                filter(l -> l.contains(username.toUpperCase())).
                map(p -> p.split(" = ")[1]).
                findAny().orElse(null);
    }

    public Authentication() {
        Given("I have username and password", () -> {
            Assert.assertNotNull(username);
            Assert.assertNotNull(password);
        });
        When("I try to connect to the LocalEGA inbox via SFTP using these credentials", () -> {
            try {
                SSHClient ssh = new SSHClient();
                ssh.addHostKeyVerifier(new PromiscuousVerifier());
                ssh.connect("localhost", 2222);
                ssh.authPassword(username, password);
                sftp = ssh.newSFTPClient();
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
        Then("the operation is successful", () -> {
            try {
                Assert.assertEquals("inbox", sftp.ls("/").iterator().next().getName());
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
    }

}